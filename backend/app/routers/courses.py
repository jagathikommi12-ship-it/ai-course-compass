from fastapi import APIRouter, Depends, HTTPException

from app.auth import CurrentUser, get_current_user
from app.models import CoursePrereqsOut, CourseOut, PrereqRefOut
from app.services import catalog_repo
from app.services.requirement_engine import (
    CourseFulfillment,
    FULFILLING_STATUSES,
    prereq_groups_with_grades_for,
    prereq_ref_satisfied,
    prereqs_satisfied_with_grades,
)

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseOut])
def list_courses(_: CurrentUser = Depends(get_current_user)):
    return [
        CourseOut(
            code=c.code,
            title=c.title,
            description=c.description,
            credits=c.credits,
            department=c.department,
            cross_listed_as=list(c.cross_listed_as),
            notes=c.notes,
        )
        for c in catalog_repo.fetch_courses()
    ]


@router.get("/{code}/prereqs", response_model=CoursePrereqsOut)
def get_course_prereqs(code: str, user: CurrentUser = Depends(get_current_user)):
    """
    Prerequisite Explorer: every PATHWAY that satisfies this course's
    prerequisites (AND within a path, OR across paths), each course paired
    with the minimum grade it requires and whether the requesting user has
    actually met it — not just a flat list, since which path applies is a
    per-student choice (e.g. COMPSCI 589 via MATH 545+COMPSCI 240+STATISTC
    315 at a C, OR via MATH 233+COMPSCI 240 at a B+).
    """
    courses = {c.code: c for c in catalog_repo.fetch_courses()}
    if code not in courses:
        raise HTTPException(status_code=404, detail=f"Unknown course code '{code}'")

    edges = catalog_repo.fetch_prereq_edges()
    fulfillment = {
        row["course_code"]: CourseFulfillment(status=row["status"], grade=row.get("grade"))
        for row in catalog_repo.fetch_planned_courses(user.user_id)
        if row["status"] in FULFILLING_STATUSES
    }

    prereq_groups_out = [
        [
            PrereqRefOut(
                code=prereq_code,
                min_grade=min_grade,
                satisfied=prereq_ref_satisfied(prereq_code, min_grade, fulfillment),
            )
            for prereq_code, min_grade in group
        ]
        for group in prereq_groups_with_grades_for(code, edges)
    ]

    return CoursePrereqsOut(
        code=code,
        title=courses[code].title,
        prereqs_met=prereqs_satisfied_with_grades(code, fulfillment, edges),
        prereq_groups=prereq_groups_out,
    )
