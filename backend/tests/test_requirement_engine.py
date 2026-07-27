from app.services.requirement_engine import (
    Course,
    PrereqEdge,
    RequirementCategory,
    RequirementCourseLink,
    category_status,
    eligible_next_courses,
    find_double_counted_courses,
    flag_ambiguous_courses,
    missing_prereq_options,
    prereqs_satisfied,
)

EDGES = [
    PrereqEdge("CS 187", "CS 121", 0),
    PrereqEdge("CS 230", "CS 187", 0),
    PrereqEdge("CS 250", "CS 187", 0),
    # CS 311 satisfiable via (CS 230 AND CS 250) OR (CS 220 alone)
    PrereqEdge("CS 311", "CS 230", 0),
    PrereqEdge("CS 311", "CS 250", 0),
    PrereqEdge("CS 311", "CS 220", 1),
]


def test_no_prereqs_always_satisfied():
    assert prereqs_satisfied("CS 121", set(), EDGES) is True


def test_and_group_requires_all():
    assert prereqs_satisfied("CS 187", {"CS 121"}, EDGES) is True
    assert prereqs_satisfied("CS 187", set(), EDGES) is False


def test_or_of_and_groups():
    # Satisfies via the AND path
    assert prereqs_satisfied("CS 311", {"CS 230", "CS 250"}, EDGES) is True
    # Satisfies via the alternate single-course path
    assert prereqs_satisfied("CS 311", {"CS 220"}, EDGES) is True
    # Partial progress on the AND path isn't enough
    assert prereqs_satisfied("CS 311", {"CS 230"}, EDGES) is False


def test_missing_prereq_options_reports_all_groups():
    missing = missing_prereq_options("CS 311", set(), EDGES)
    assert ["CS 230", "CS 250"] in missing
    assert ["CS 220"] in missing


def test_missing_prereq_options_empty_when_unlocked():
    assert missing_prereq_options("CS 311", {"CS 220"}, EDGES) == []


def test_eligible_next_courses_recommendation_mode():
    all_codes = ["CS 121", "CS 187", "CS 230", "CS 250", "CS 311"]
    completed = {"CS 121", "CS 187"}
    eligible = eligible_next_courses(all_codes, completed, EDGES)
    assert set(eligible) == {"CS 230", "CS 250"}
    assert "CS 311" not in eligible  # not reachable yet
    assert "CS 121" not in eligible  # already completed


def test_category_status_by_course_count():
    category = RequirementCategory(id="cat1", program_id="p1", name="CS Foundation", min_courses=3)
    links = [
        RequirementCourseLink("cat1", "CS 121"),
        RequirementCourseLink("cat1", "CS 187"),
        RequirementCourseLink("cat1", "CS 230"),
    ]
    courses_by_code = {c.code: c for c in [Course("CS 121", "x"), Course("CS 187", "y"), Course("CS 230", "z")]}

    status = category_status(category, links, {"CS 121", "CS 187"}, courses_by_code)
    assert status.satisfied is False
    assert status.still_needed == 1

    status_done = category_status(category, links, {"CS 121", "CS 187", "CS 230"}, courses_by_code)
    assert status_done.satisfied is True
    assert status_done.still_needed == 0


def test_category_status_by_credits():
    category = RequirementCategory(id="cat2", program_id="p1", name="Free electives", min_credits=6)
    links = [
        RequirementCourseLink("cat2", "CS 320"),
        RequirementCourseLink("cat2", "CS 345"),
    ]
    courses_by_code = {
        "CS 320": Course("CS 320", "x", credits=3),
        "CS 345": Course("CS 345", "y", credits=4),
    }
    status = category_status(category, links, {"CS 320"}, courses_by_code)
    assert status.satisfied is False
    status2 = category_status(category, links, {"CS 320", "CS 345"}, courses_by_code)
    assert status2.satisfied is True


def test_find_double_counted_courses():
    links = [
        RequirementCourseLink("catA", "CS 345"),
        RequirementCourseLink("catB", "CS 345"),
        RequirementCourseLink("catA", "CS 320"),
    ]
    doubled = find_double_counted_courses(links)
    assert doubled == {"CS 345": ["catA", "catB"]}


def test_flag_ambiguous_courses():
    courses = [
        Course("CS 240", "x", cross_listed_as=("STAT 240",)),
        Course("CS 121", "y"),
        Course("CS 345", "z", notes="Only counts under INFO 345."),
    ]
    flagged = flag_ambiguous_courses(courses)
    assert "CS 240" in flagged and "STAT 240" in flagged["CS 240"]
    assert "CS 121" not in flagged
    assert "Only counts" in flagged["CS 345"]
