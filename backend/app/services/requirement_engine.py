"""
Deterministic requirement-checking logic. This is intentionally kept free of
any LLM/agent code: it is the "ground truth" calculator that both the REST
endpoints and the Claude agent's tools call into, so the agent can never
hallucinate whether a requirement is actually satisfied — it can only ask
this engine and relay the answer.
"""

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Course:
    code: str
    title: str
    description: str = ""
    credits: float = 3
    department: str = ""
    cross_listed_as: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class PrereqEdge:
    course_code: str
    prereq_code: str
    group_id: int = 0


@dataclass(frozen=True)
class RequirementCategory:
    id: str
    program_id: str
    name: str
    min_courses: int | None = None
    min_credits: float | None = None
    sort_order: int = 0
    description: str = ""


@dataclass(frozen=True)
class RequirementCourseLink:
    category_id: str
    course_code: str
    satisfies_note: str = ""


def _prereq_groups(course_code: str, edges: list[PrereqEdge]) -> list[list[str]]:
    """Groups this course's prereq edges by group_id (AND within a group, OR across groups)."""
    groups: dict[int, list[str]] = defaultdict(list)
    for edge in edges:
        if edge.course_code == course_code:
            groups[edge.group_id].append(edge.prereq_code)
    return list(groups.values())


def prereqs_satisfied(course_code: str, completed: set[str], edges: list[PrereqEdge]) -> bool:
    groups = _prereq_groups(course_code, edges)
    if not groups:
        return True
    return any(all(prereq in completed for prereq in group) for group in groups)


def missing_prereq_options(
    course_code: str, completed: set[str], edges: list[PrereqEdge]
) -> list[list[str]]:
    """
    Returns the prereq groups that are NOT yet fully satisfied, each as the
    list of still-missing courses within that group. An empty return means
    the course is unlocked. Multiple groups mean "any ONE of these paths".
    """
    groups = _prereq_groups(course_code, edges)
    if not groups:
        return []
    if any(all(c in completed for c in group) for group in groups):
        return []
    return [[c for c in group if c not in completed] for group in groups]


def eligible_next_courses(
    all_course_codes: list[str], completed: set[str], edges: list[PrereqEdge]
) -> list[str]:
    """Recommendation Mode: courses not yet taken whose prereqs are fully met."""
    return [
        code
        for code in all_course_codes
        if code not in completed and prereqs_satisfied(code, completed, edges)
    ]


@dataclass
class CategoryStatus:
    category_id: str
    name: str
    required_courses: int | None
    required_credits: float | None
    completed_courses: list[str]
    satisfied: bool
    still_needed: int  # 0 if satisfied


def category_status(
    category: RequirementCategory,
    links: list[RequirementCourseLink],
    completed: set[str],
    courses_by_code: dict[str, Course],
) -> CategoryStatus:
    eligible_codes = [link.course_code for link in links if link.category_id == category.id]
    completed_in_category = [c for c in eligible_codes if c in completed]

    if category.min_credits is not None:
        earned_credits = sum(courses_by_code[c].credits for c in completed_in_category if c in courses_by_code)
        satisfied = earned_credits >= category.min_credits
        still_needed = 0 if satisfied else int(category.min_credits - earned_credits)
    else:
        required = category.min_courses or 1
        satisfied = len(completed_in_category) >= required
        still_needed = max(0, required - len(completed_in_category))

    return CategoryStatus(
        category_id=category.id,
        name=category.name,
        required_courses=category.min_courses,
        required_credits=category.min_credits,
        completed_courses=completed_in_category,
        satisfied=satisfied,
        still_needed=still_needed,
    )


def find_double_counted_courses(
    links: list[RequirementCourseLink],
) -> dict[str, list[str]]:
    """course_code -> list of category_ids it appears under. len > 1 means it can double-count."""
    seen: dict[str, list[str]] = defaultdict(list)
    for link in links:
        seen[link.course_code].append(link.category_id)
    return {code: cats for code, cats in seen.items() if len(cats) > 1}


def flag_ambiguous_courses(courses: list[Course]) -> dict[str, str]:
    """
    Surfaces courses with cross-listing or freeform notes that could affect
    whether they count (e.g. "only counts under the other cross-listed code").
    Returns course_code -> the note to show the user, so the agent/UI can
    say "this might not count as you expect" rather than silently asserting
    it does.
    """
    flagged = {}
    for course in courses:
        if course.cross_listed_as or course.notes:
            parts = []
            if course.cross_listed_as:
                parts.append(f"Cross-listed as {', '.join(course.cross_listed_as)}.")
            if course.notes:
                parts.append(course.notes)
            flagged[course.code] = " ".join(parts)
    return flagged


# ---------------------------------------------------------------------------
# Semester planner: credits tracking + term-aware prerequisite checking
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlannedCourse:
    course_code: str
    term_position: int | None  # None = unscheduled (checked off or backlog); otherwise the term's sequence position
    status: str  # 'planned' | 'completed'
    locked: bool  # done, or certain (currently enrolled) — can't be casually dragged/removed


@dataclass(frozen=True)
class CreditsSummary:
    total_required: float
    scheduled_credits: float  # sum of credits for every course placed in some term
    locked_credits: float  # sum of credits for locked (done/certain) courses
    remaining_credits: float  # max(0, total_required - locked_credits)


def compute_credits_summary(
    total_required: float,
    planned: list[PlannedCourse],
    courses_by_code: dict[str, Course],
) -> CreditsSummary:
    scheduled = sum(
        courses_by_code[p.course_code].credits
        for p in planned
        if p.term_position is not None and p.course_code in courses_by_code
    )
    locked = sum(
        courses_by_code[p.course_code].credits
        for p in planned
        if p.locked and p.course_code in courses_by_code
    )
    remaining = max(0.0, total_required - locked)
    return CreditsSummary(
        total_required=total_required,
        scheduled_credits=scheduled,
        locked_credits=locked,
        remaining_credits=remaining,
    )


def _codes_in_earlier_terms(target_position: int, planned: list[PlannedCourse]) -> set[str]:
    return {
        p.course_code
        for p in planned
        if p.term_position is not None and p.term_position < target_position
    }


def prereqs_satisfied_for_term(
    course_code: str,
    target_position: int,
    planned: list[PlannedCourse],
    edges: list[PrereqEdge],
) -> bool:
    """
    A course can be scheduled into a term if its prerequisites are all
    scheduled into STRICTLY EARLIER terms in the same plan (being scheduled
    for the future is enough for planning purposes — it doesn't need to
    already be marked 'completed').
    """
    return prereqs_satisfied(course_code, _codes_in_earlier_terms(target_position, planned), edges)


def missing_prereqs_for_term(
    course_code: str,
    target_position: int,
    planned: list[PlannedCourse],
    edges: list[PrereqEdge],
) -> list[list[str]]:
    """Same shape as missing_prereq_options: empty if satisfied, else the still-missing AND-groups."""
    return missing_prereq_options(course_code, _codes_in_earlier_terms(target_position, planned), edges)


def format_missing_prereq_message(course_code: str, missing_options: list[list[str]]) -> str:
    """Turns [["CICS 160"]] into a plain-English popup message naming exactly what's missing."""
    if not missing_options:
        return f"{course_code} has no unmet prerequisites."
    paths = [" and ".join(group) for group in missing_options]
    if len(paths) == 1:
        return f"You need to take {paths[0]} in an earlier term before {course_code}."
    return f"You need to take ({') or ('.join(paths)}) in an earlier term before {course_code}."


def generate_regular_terms(target_semesters: int, start_type: str = "fall") -> list[dict]:
    """
    Builds the initial alternating Fall/Spring term sequence for a fresh plan,
    e.g. target_semesters=8 -> Year 1 Fall, Year 1 Spring, Year 2 Fall, ...
    Positions are dense (0..N-1); summer/winter terms are inserted later by
    shifting positions, so they don't need to be reserved for up front.
    """
    types = ["fall", "spring"] if start_type == "fall" else ["spring", "fall"]
    terms = []
    for i in range(target_semesters):
        term_type = types[i % 2]
        year = i // 2 + 1
        terms.append(
            {
                "term_type": term_type,
                "label": f"Year {year} - {term_type.capitalize()}",
                "position": i,
            }
        )
    return terms
