from fastapi import APIRouter, Depends, HTTPException

from app.auth import CurrentUser, get_current_user
from app.models import (
    CategoryStatusOut,
    ChecklistCategoryOut,
    ChecklistCourseOut,
    ProgramChecklistOut,
    ProgramStatusOut,
)
from app.services import catalog_repo
from app.services.requirement_engine import (
    category_status,
    find_double_counted_courses,
    flag_ambiguous_courses,
)

router = APIRouter(prefix="/programs", tags=["requirements"])


@router.get("")
def list_programs(_: CurrentUser = Depends(get_current_user)):
    return catalog_repo.fetch_programs()


@router.get("/{program_id}/status", response_model=ProgramStatusOut)
def get_program_status(program_id: str, user: CurrentUser = Depends(get_current_user)):
    """
    The core "what am I still missing for my major/minor" answer: every
    requirement category for this program, whether it's satisfied, and
    which courses can be counted more than once or might not count due to
    cross-listing — computed fresh from the deterministic engine, not
    guessed by an LLM.
    """
    programs = {p["id"]: p for p in catalog_repo.fetch_programs()}
    if program_id not in programs:
        raise HTTPException(status_code=404, detail="Unknown program_id")

    categories = catalog_repo.fetch_categories(program_id=program_id)
    if not categories:
        return ProgramStatusOut(
            program_id=program_id,
            program_name=programs[program_id]["name"],
            categories=[],
            double_counted_courses={},
            ambiguous_courses={},
        )

    category_ids = [c.id for c in categories]
    links = catalog_repo.fetch_requirement_links(category_ids=category_ids)
    completed = catalog_repo.fetch_completed_course_codes(user.user_id)
    courses_by_code = {c.code: c for c in catalog_repo.fetch_courses()}

    statuses = [
        category_status(cat, links, completed, courses_by_code) for cat in categories
    ]
    relevant_codes = {link.course_code for link in links}
    ambiguous = flag_ambiguous_courses(
        [c for code, c in courses_by_code.items() if code in relevant_codes]
    )

    return ProgramStatusOut(
        program_id=program_id,
        program_name=programs[program_id]["name"],
        categories=[
            CategoryStatusOut(
                category_id=s.category_id,
                name=s.name,
                required_courses=s.required_courses,
                required_credits=s.required_credits,
                completed_courses=s.completed_courses,
                satisfied=s.satisfied,
                still_needed=s.still_needed,
            )
            for s in statuses
        ],
        double_counted_courses=find_double_counted_courses(links),
        ambiguous_courses=ambiguous,
    )


@router.get("/{program_id}/checklist", response_model=ProgramChecklistOut)
def get_program_checklist(program_id: str, user: CurrentUser = Depends(get_current_user)):
    """
    Every course in every requirement category for this program (not just
    the ones already completed), for rendering the full checklist with
    section separations. Each course's status/locked comes from the user's
    plan (user_planned_courses) — 'not_started' if they have no row there.
    """
    programs = {p["id"]: p for p in catalog_repo.fetch_programs()}
    if program_id not in programs:
        raise HTTPException(status_code=404, detail="Unknown program_id")

    categories = sorted(catalog_repo.fetch_categories(program_id=program_id), key=lambda c: c.sort_order)
    category_ids = [c.id for c in categories]
    links = catalog_repo.fetch_requirement_links(category_ids=category_ids)
    courses_by_code = {c.code: c for c in catalog_repo.fetch_courses()}

    planned_by_code = {row["course_code"]: row for row in catalog_repo.fetch_planned_courses(user.user_id)}

    links_by_category: dict[str, list] = {}
    for link in links:
        links_by_category.setdefault(link.category_id, []).append(link)

    checklist_categories = []
    all_codes_seen: set[str] = set()
    all_completed_seen: set[str] = set()

    for cat in categories:
        cat_links = links_by_category.get(cat.id, [])
        courses_out = []
        completed_count = 0
        for link in cat_links:
            course = courses_by_code.get(link.course_code)
            if course is None:
                continue
            plan_row = planned_by_code.get(link.course_code)
            status = plan_row["status"] if plan_row else "not_started"
            locked = plan_row["locked"] if plan_row else False
            if status == "completed":
                completed_count += 1
                all_completed_seen.add(link.course_code)
            all_codes_seen.add(link.course_code)
            courses_out.append(
                ChecklistCourseOut(
                    code=course.code,
                    title=course.title,
                    credits=course.credits,
                    satisfies_note=link.satisfies_note,
                    status=status,
                    locked=locked,
                )
            )
        checklist_categories.append(
            ChecklistCategoryOut(
                category_id=cat.id,
                name=cat.name,
                description=cat.description,
                required_courses=cat.min_courses,
                required_credits=cat.min_credits,
                courses=courses_out,
                completed_count=completed_count,
                total_count=len(courses_out),
            )
        )

    return ProgramChecklistOut(
        program_id=program_id,
        program_name=programs[program_id]["name"],
        categories=checklist_categories,
        total_completed=len(all_completed_seen),
        total_courses=len(all_codes_seen),
    )
