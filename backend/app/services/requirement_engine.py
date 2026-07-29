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
    min_grade: str = "C"  # e.g. COMPSCI 514 needs "B+" in its prereqs, COMPSCI 575 needs "B"


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
    is_required: bool = True  # False for courses that are one of several alternatives in a "mixed" category


def _prereq_groups(course_code: str, edges: list[PrereqEdge]) -> list[list[str]]:
    """Groups this course's prereq edges by group_id (AND within a group, OR across groups)."""
    groups: dict[int, list[str]] = defaultdict(list)
    for edge in edges:
        if edge.course_code == course_code:
            groups[edge.group_id].append(edge.prereq_code)
    return list(groups.values())


def prereq_groups_for(course_code: str, edges: list[PrereqEdge]) -> list[list[str]]:
    """Public accessor: this course's prereq groups (AND within a group, OR across groups)."""
    return _prereq_groups(course_code, edges)


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


# ---------------------------------------------------------------------------
# Grade-aware prerequisite checking
#
# course_prerequisites.min_grade has been seeded since day one (e.g. COMPSCI
# 514 needs a B+ in COMPSCI 240/311, COMPSCI 575 needs a B) but the functions
# above only ever checked whether a prereq was DONE, never the grade. These
# variants take each course's actual status/grade and enforce min_grade too.
# Term-scheduling (prereqs_satisfied_for_term) deliberately stays grade-blind
# — you don't know your grade yet when you're just planning a future term —
# so only the "is this actually, truly satisfied" call sites (the checklist
# and Recommendation Mode) use these.
# ---------------------------------------------------------------------------

GRADE_POINTS = {
    "A": 4.0, "A-": 3.7,
    "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7,
    "D+": 1.3, "D": 1.0, "D-": 0.7,
    "F": 0.0,
}


@dataclass(frozen=True)
class CourseFulfillment:
    status: str  # 'completed' | 'skipped' | 'credited'
    grade: str | None = None  # letter grade actually earned; only meaningful when status == 'completed'


def grade_meets_minimum(grade: str | None, min_grade: str) -> bool:
    """
    grade=None means no grade was recorded (e.g. an older row from before
    grade-tracking existed) — treat that as meeting only the default 'C' bar,
    so nothing regresses for courses nobody entered a grade for.
    """
    if grade is None:
        return GRADE_POINTS.get(min_grade, 2.0) <= GRADE_POINTS["C"]
    return GRADE_POINTS.get(grade, 0.0) >= GRADE_POINTS.get(min_grade, 2.0)


def _prereq_groups_detailed(course_code: str, edges: list[PrereqEdge]) -> list[list[PrereqEdge]]:
    groups: dict[int, list[PrereqEdge]] = defaultdict(list)
    for edge in edges:
        if edge.course_code == course_code:
            groups[edge.group_id].append(edge)
    return list(groups.values())


def prereq_groups_with_grades_for(course_code: str, edges: list[PrereqEdge]) -> list[list[tuple[str, str]]]:
    """Same AND/OR grouping as prereq_groups_for, but pairing each prereq code with its min_grade."""
    return [[(e.prereq_code, e.min_grade) for e in group] for group in _prereq_groups_detailed(course_code, edges)]


def prereq_ref_satisfied(prereq_code: str, min_grade: str, fulfillment: dict[str, CourseFulfillment]) -> bool:
    """Has the user met this specific prereq at the required grade (or skipped/credited it)?"""
    course = fulfillment.get(prereq_code)
    if course is None:
        return False
    if course.status in EXEMPT_STATUSES:
        return True  # skipped/credited — there's no course grade to check
    return grade_meets_minimum(course.grade, min_grade)


def prereqs_satisfied_with_grades(
    course_code: str, fulfillment: dict[str, CourseFulfillment], edges: list[PrereqEdge]
) -> bool:
    groups = _prereq_groups_detailed(course_code, edges)
    if not groups:
        return True
    return any(
        all(prereq_ref_satisfied(edge.prereq_code, edge.min_grade, fulfillment) for edge in group)
        for group in groups
    )


def eligible_next_courses_with_grades(
    all_course_codes: list[str], fulfillment: dict[str, CourseFulfillment], edges: list[PrereqEdge]
) -> list[str]:
    """Recommendation Mode: courses not yet taken/exempted whose prereqs are truly met (grades included)."""
    return [
        code
        for code in all_course_codes
        if code not in fulfillment and prereqs_satisfied_with_grades(code, fulfillment, edges)
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


#: Statuses that mean "this requirement is handled" for prereq-checking and
#: the checklist's done-count, even though the course was never scheduled
#: into a term: it was checked off, skipped (e.g. tested out of it), or
#: satisfied via outside credit (AP/IB/transfer).
FULFILLING_STATUSES = {"completed", "skipped", "credited"}

#: Statuses whose credits count toward the credits-earned tracker. Skipped
#: courses deliberately do NOT contribute credits — there's nothing to add.
CREDIT_BEARING_STATUSES = {"completed", "credited"}

#: Statuses that must never be scheduled into a term — they represent a
#: course the student isn't taking the normal way at all.
EXEMPT_STATUSES = {"skipped", "credited"}


@dataclass(frozen=True)
class PlannedCourse:
    course_code: str
    term_position: int | None  # None = unscheduled (checked off, exempt, or backlog); otherwise the term's sequence position
    status: str  # 'planned' | 'completed' | 'skipped' | 'credited'


@dataclass(frozen=True)
class CreditsSummary:
    total_required: float
    scheduled_credits: float  # sum of credits for every course placed in some term
    completed_credits: float  # incoming (AP/IB/transfer) credits + credits for completed/credited courses
    remaining_credits: float  # max(0, total_required - completed_credits)


def compute_credits_summary(
    total_required: float,
    incoming_credits: float,
    planned: list[PlannedCourse],
    courses_by_code: dict[str, Course],
) -> CreditsSummary:
    scheduled = sum(
        courses_by_code[p.course_code].credits
        for p in planned
        if p.term_position is not None and p.course_code in courses_by_code
    )
    earned = sum(
        courses_by_code[p.course_code].credits
        for p in planned
        if p.status in CREDIT_BEARING_STATUSES and p.course_code in courses_by_code
    )
    completed = incoming_credits + earned
    remaining = max(0.0, total_required - completed)
    return CreditsSummary(
        total_required=total_required,
        scheduled_credits=scheduled,
        completed_credits=completed,
        remaining_credits=remaining,
    )


def _codes_satisfying_prereq(target_position: int, planned: list[PlannedCourse]) -> set[str]:
    """
    A prereq course counts as satisfied for scheduling something into
    `target_position` if it's already fulfilled outright (completed,
    skipped, or credited — regardless of whether it's on the calendar at
    all), or if it's scheduled into a strictly earlier term (planning ahead
    is enough; it doesn't need to already be marked done).
    """
    fulfilled = {p.course_code for p in planned if p.status in FULFILLING_STATUSES}
    scheduled_earlier = {
        p.course_code for p in planned if p.term_position is not None and p.term_position < target_position
    }
    return fulfilled | scheduled_earlier


def prereqs_satisfied_for_term(
    course_code: str,
    target_position: int,
    planned: list[PlannedCourse],
    edges: list[PrereqEdge],
) -> bool:
    """A course can be scheduled into a term once all its prerequisites are satisfied (see _codes_satisfying_prereq)."""
    return prereqs_satisfied(course_code, _codes_satisfying_prereq(target_position, planned), edges)


def missing_prereqs_for_term(
    course_code: str,
    target_position: int,
    planned: list[PlannedCourse],
    edges: list[PrereqEdge],
) -> list[list[str]]:
    """Same shape as missing_prereq_options: empty if satisfied, else the still-missing AND-groups."""
    return missing_prereq_options(course_code, _codes_satisfying_prereq(target_position, planned), edges)


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
