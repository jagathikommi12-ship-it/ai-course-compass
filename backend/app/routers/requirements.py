from fastapi import APIRouter, Depends, HTTPException

from app.auth import CurrentUser, get_current_user
from app.models import (
    CategoryStatusOut,
    ChecklistCategoryOut,
    ChecklistCourseOut,
    PrereqRefOut,
    ProgramChecklistOut,
    ProgramStatusOut,
)
from app.services import catalog_repo
from app.services.requirement_engine import (
    category_status,
    find_double_counted_courses,
    flag_ambiguous_courses,
    prereq_groups_for,
    prereqs_satisfied,
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
    section separations. Each course's status comes from the user's plan
    (user_planned_courses) — 'not_started' if they have no row there.
    """
    programs = {p["id"]: p for p in catalog_repo.fetch_programs()}
    if program_id not in programs:
        raise HTTPException(status_code=404, detail="Unknown program_id")

    categories = sorted(catalog_repo.fetch_categories(program_id=program_id), key=lambda c: c.sort_order)
    category_ids = [c.id for c in categories]
    links = catalog_repo.fetch_requirement_links(category_ids=category_ids)
    courses_by_code = {c.code: c for c in catalog_repo.fetch_courses()}
    edges = catalog_repo.fetch_prereq_edges()
    ambiguous_notes = flag_ambiguous_courses(list(courses_by_code.values()))

    planned_by_code = {row["course_code"]: row for row in catalog_repo.fetch_planned_courses(user.user_id)}
    completed_codes = {code for code, row in planned_by_code.items() if row["status"] == "completed"}

    links_by_category: dict[str, list] = {}
    for link in links:
        links_by_category.setdefault(link.category_id, []).append(link)

    checklist_categories = []
    all_codes_seen: set[str] = set()
    all_completed_seen: set[str] = set()

    for cat in categories:
        cat_links = links_by_category.get(cat.id, [])
        valid_links = [link for link in cat_links if link.course_code in courses_by_code]
        # If the category requires literally every listed course, each one is mandatory;
        # otherwise it's a "pick some subset" category and every course in it is a choice.
        mandatory = cat.min_courses is not None and cat.min_courses >= len(valid_links)

        courses_out = []
        completed_count = 0
        for link in valid_links:
            course = courses_by_code[link.course_code]
            plan_row = planned_by_code.get(link.course_code)
            status = plan_row["status"] if plan_row else "not_started"
            if status == "completed":
                completed_count += 1
                all_completed_seen.add(link.course_code)
            all_codes_seen.add(link.course_code)

            groups = prereq_groups_for(link.course_code, edges)
            prereq_groups_out = [
                [PrereqRefOut(code=prereq_code, satisfied=prereq_code in completed_codes) for prereq_code in group]
                for group in groups
            ]

            courses_out.append(
                ChecklistCourseOut(
                    code=course.code,
                    title=course.title,
                    credits=course.credits,
                    satisfies_note=link.satisfies_note,
                    ambiguous_note=ambiguous_notes.get(course.code, ""),
                    status=status,
                    mandatory=mandatory,
                    prereqs_met=prereqs_satisfied(link.course_code, completed_codes, edges),
                    prereq_groups=prereq_groups_out,
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
