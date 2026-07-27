from fastapi import APIRouter, Depends

from app.auth import CurrentUser, get_current_user
from app.models import CompletedCourseIn, CourseOut, RecommendationOut
from app.services import catalog_repo
from app.services.requirement_engine import eligible_next_courses

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
def get_recommendations(user: CurrentUser = Depends(get_current_user)):
    """Recommendation Mode: every course the user is now eligible to take."""
    courses = catalog_repo.fetch_courses()
    edges = catalog_repo.fetch_prereq_edges()
    completed = catalog_repo.fetch_completed_course_codes(user.user_id)

    eligible_codes = set(eligible_next_courses([c.code for c in courses], completed, edges))
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
        for c in courses
        if c.code in eligible_codes
    ]
    return RecommendationOut(eligible_courses=eligible)
