from fastapi import APIRouter, Depends, HTTPException

from app.auth import CurrentUser, get_current_user
from app.models import CourseOut, PrereqNode
from app.services import catalog_repo
from app.services.requirement_engine import missing_prereq_options, prereqs_satisfied

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


@router.get("/{code}/prereq-tree", response_model=PrereqNode)
def get_prereq_tree(
    code: str,
    max_depth: int = 6,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Recursive drill-down: click a course, see its prereqs; click one of
    those, see its prereqs, and so on. `satisfied` is evaluated against the
    requesting user's completed courses so the UI can grey out what's done.
    """
    courses = {c.code: c for c in catalog_repo.fetch_courses()}
    if code not in courses:
        raise HTTPException(status_code=404, detail=f"Unknown course code '{code}'")

    edges = catalog_repo.fetch_prereq_edges()
    completed = catalog_repo.fetch_completed_course_codes(user.user_id)

    def build(course_code: str, depth: int, visited: frozenset[str]) -> PrereqNode:
        course = courses.get(course_code)
        title = course.title if course else course_code
        satisfied = prereqs_satisfied(course_code, completed, edges)
        missing = missing_prereq_options(course_code, completed, edges)

        children: list[PrereqNode] = []
        if depth < max_depth:
            direct_prereqs = {p for group in missing for p in group} or {
                p for edge in edges if edge.course_code == course_code for p in [edge.prereq_code]
            }
            for prereq_code in sorted(direct_prereqs):
                if prereq_code in visited:
                    continue  # guard against any accidental cycle in the data
                children.append(build(prereq_code, depth + 1, visited | {course_code}))

        return PrereqNode(
            code=course_code,
            title=title,
            satisfied=satisfied,
            missing_options=missing,
            children=children,
        )

    return build(code, 0, frozenset())
