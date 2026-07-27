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
