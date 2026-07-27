from fastapi import APIRouter, Depends, HTTPException

from app.auth import CurrentUser, get_current_user
from app.models import CategoryStatusOut, ProgramStatusOut
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
