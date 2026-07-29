from fastapi import APIRouter, Depends

from app.auth import CurrentUser, get_current_user
from app.models import CompletedCourseIn, CourseOut, RecommendationOut
from app.services import catalog_repo
from app.services.requirement_engine import (
    FULFILLING_STATUSES,
    CourseFulfillment,
    eligible_next_courses_with_grades,
)

router = APIRouter(prefix="/me", tags=["progress"])


@router.get("/completed", response_model=list[str])
def get_completed(user: CurrentUser = Depends(get_current_user)):
    return sorted(catalog_repo.fetch_completed_course_codes(user.user_id))


@router.post("/completed", status_code=204)
def mark_completed(body: CompletedCourseIn, user: CurrentUser = Depends(get_current_user)):
    # user.user_id comes only from the verified JWT (see app/auth.py) — a
    # client can never mark another student's course complete by passing a
    # different id, because no id is accepted from the request body at all.
    catalog_repo.add_completed_course(user.user_id, body.course_code, body.term, body.grade)


@router.delete("/completed/{course_code}", status_code=204)
def unmark_completed(course_code: str, user: CurrentUser = Depends(get_current_user)):
    catalog_repo.remove_completed_course(user.user_id, course_code)


@router.get("/recommendations", response_model=RecommendationOut)
def get_recommendations(program_id: str | None = None, user: CurrentUser = Depends(get_current_user)):
    """
    Recommendation Mode: which courses toward this program the user is now
    eligible to take, based on what they've checked off (completed, skipped,
    or credited) in the plan checklist — never the legacy completed-courses
    table, and never courses outside the chosen program's requirements.
    """
    courses_by_code = {c.code: c for c in catalog_repo.fetch_courses()}
    edges = catalog_repo.fetch_prereq_edges()
    fulfillment = {
        row["course_code"]: CourseFulfillment(status=row["status"], grade=row.get("grade"))
        for row in catalog_repo.fetch_planned_courses(user.user_id)
        if row["status"] in FULFILLING_STATUSES
    }

    programs = catalog_repo.fetch_programs()
    program = None
    if programs:
        program = next((p for p in programs if p["id"] == program_id), programs[0]) if program_id else programs[0]

    if program:
        categories = catalog_repo.fetch_categories(program_id=program["id"])
        links = catalog_repo.fetch_requirement_links(category_ids=[c.id for c in categories])
        relevant_codes = sorted({link.course_code for link in links if link.course_code in courses_by_code})
    else:
        relevant_codes = sorted(courses_by_code)

    eligible_codes = set(eligible_next_courses_with_grades(relevant_codes, fulfillment, edges))
    eligible = [
        CourseOut(
            code=c.code,
            title=c.title,
            description=c.description,
            credits=c.credits,
            department=c.department,
            cross_listed_as=list(c.cross_listed_as),
            notes=c.notes,
        )
        for code, c in courses_by_code.items()
        if code in eligible_codes
    ]
    return RecommendationOut(eligible_courses=eligible)
