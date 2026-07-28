from fastapi import APIRouter, Depends, HTTPException

from app.auth import CurrentUser, get_current_user
from app.models import (
    AddTermIn,
    CreditsSummaryOut,
    PlanCourseIn,
    PlanOut,
    PlannedCourseOut,
    PlanSettingsIn,
    PlanSettingsOut,
    TermOut,
)
from app.services import catalog_repo
from app.services.requirement_engine import (
    PlannedCourse,
    compute_credits_summary,
    format_missing_prereq_message,
    generate_regular_terms,
    missing_prereqs_for_term,
    prereqs_satisfied_for_term,
)

router = APIRouter(prefix="/me/plan", tags=["plan"])


def _planned_courses_with_positions(user_id: str) -> tuple[list[PlannedCourse], dict[str, dict], list[dict]]:
    """Returns (planned domain objects with term positions filled in, terms_by_id, raw rows)."""
    terms = catalog_repo.fetch_terms(user_id)
    terms_by_id = {t["id"]: t for t in terms}
    rows = catalog_repo.fetch_planned_courses(user_id)
    planned = [
        PlannedCourse(
            course_code=row["course_code"],
            term_position=terms_by_id[row["term_id"]]["position"] if row.get("term_id") else None,
            status=row["status"],
            locked=row["locked"],
        )
        for row in rows
    ]
    return planned, terms_by_id, rows


@router.get("", response_model=PlanOut)
def get_plan(program_id: str | None = None, user: CurrentUser = Depends(get_current_user)):
    settings_row = catalog_repo.fetch_plan_settings(user.user_id)
    terms = catalog_repo.fetch_terms(user.user_id)
    planned, _, raw_rows = _planned_courses_with_positions(user.user_id)
    courses_by_code = {c.code: c for c in catalog_repo.fetch_courses()}

    programs = catalog_repo.fetch_programs()
    program = None
    if programs:
        program = next((p for p in programs if p["id"] == program_id), programs[0]) if program_id else programs[0]
    total_required = program["total_credits_required"] if program else 120

    summary = compute_credits_summary(total_required, planned, courses_by_code)

    return PlanOut(
        settings=PlanSettingsOut(**settings_row) if settings_row else None,
        terms=[TermOut(**t) for t in terms],
        planned_courses=[
            PlannedCourseOut(
                course_code=row["course_code"],
                title=courses_by_code[row["course_code"]].title if row["course_code"] in courses_by_code else row["course_code"],
                credits=courses_by_code[row["course_code"]].credits if row["course_code"] in courses_by_code else 0,
                term_id=row.get("term_id"),
                status=row["status"],
                locked=row["locked"],
            )
            for row in raw_rows
        ],
        credits_summary=CreditsSummaryOut(
            total_required=summary.total_required,
            scheduled_credits=summary.scheduled_credits,
            locked_credits=summary.locked_credits,
            remaining_credits=summary.remaining_credits,
        ),
    )


@router.put("/settings", response_model=list[TermOut])
def update_plan_settings(body: PlanSettingsIn, user: CurrentUser = Depends(get_current_user)):
    """
    Upserts plan settings. On the FIRST call for a user (no terms exist yet),
    this also generates the alternating Fall/Spring term sequence. Later
    calls just update the numbers — existing terms (and whatever's scheduled
    into them) are left alone; add/remove terms individually after that.
    """
    catalog_repo.upsert_plan_settings(user.user_id, body.incoming_credits, body.target_semesters)

    existing_terms = catalog_repo.fetch_terms(user.user_id)
    if not existing_terms:
        generated = generate_regular_terms(body.target_semesters)
        catalog_repo.insert_terms(user.user_id, generated)

    return [TermOut(**t) for t in catalog_repo.fetch_terms(user.user_id)]


@router.post("/terms", response_model=TermOut)
def add_term(body: AddTermIn, user: CurrentUser = Depends(get_current_user)):
    if body.term_type not in ("summer", "winter", "fall", "spring"):
        raise HTTPException(status_code=400, detail="Invalid term_type")
    insert_position = body.after_position + 1
    catalog_repo.shift_term_positions(user.user_id, insert_position, delta=1)
    created = catalog_repo.insert_term(user.user_id, body.term_type, body.label, insert_position)
    return TermOut(**created)


@router.delete("/terms/{term_id}", status_code=204)
def remove_term(term_id: str, user: CurrentUser = Depends(get_current_user)):
    catalog_repo.delete_term(user.user_id, term_id)


@router.post("/courses", response_model=PlannedCourseOut)
def upsert_course(body: PlanCourseIn, user: CurrentUser = Depends(get_current_user)):
    """
    Schedules (or updates) a course in the user's plan. If term_id is set,
    the course's prerequisites must already be scheduled in a STRICTLY
    earlier term (any status) — otherwise this returns 400 with a message
    naming exactly what's missing, for the frontend to show as a popup.
    """
    courses_by_code = {c.code: c for c in catalog_repo.fetch_courses()}
    if body.course_code not in courses_by_code:
        raise HTTPException(status_code=404, detail=f"Unknown course code '{body.course_code}'")

    if body.term_id is not None:
        terms_by_id = {t["id"]: t for t in catalog_repo.fetch_terms(user.user_id)}
        target_term = terms_by_id.get(body.term_id)
        if target_term is None:
            raise HTTPException(status_code=404, detail="Unknown term_id")

        edges = catalog_repo.fetch_prereq_edges()
        existing_rows = [r for r in catalog_repo.fetch_planned_courses(user.user_id) if r["course_code"] != body.course_code]
        planned = [
            PlannedCourse(
                course_code=r["course_code"],
                term_position=terms_by_id[r["term_id"]]["position"] if r.get("term_id") in terms_by_id else None,
                status=r["status"],
                locked=r["locked"],
            )
            for r in existing_rows
        ]
        if not prereqs_satisfied_for_term(body.course_code, target_term["position"], planned, edges):
            missing = missing_prereqs_for_term(body.course_code, target_term["position"], planned, edges)
            raise HTTPException(
                status_code=400,
                detail={
                    "message": format_missing_prereq_message(body.course_code, missing),
                    "missing_options": missing,
                },
            )

    row = catalog_repo.upsert_planned_course(user.user_id, body.course_code, body.term_id, body.status, body.locked)
    course = courses_by_code[body.course_code]
    return PlannedCourseOut(
        course_code=row["course_code"],
        title=course.title,
        credits=course.credits,
        term_id=row.get("term_id"),
        status=row["status"],
        locked=row["locked"],
    )


@router.delete("/courses/{course_code}", status_code=204)
def remove_course(course_code: str, user: CurrentUser = Depends(get_current_user)):
    existing = catalog_repo.fetch_planned_course(user.user_id, course_code)
    if existing and existing["locked"]:
        raise HTTPException(status_code=400, detail="Unlock this course before removing it from your plan.")
    catalog_repo.delete_planned_course(user.user_id, course_code)
