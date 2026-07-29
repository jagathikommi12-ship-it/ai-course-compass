from app.services.requirement_engine import (
    Course,
    CourseFulfillment,
    PlannedCourse,
    PrereqEdge,
    RequirementCategory,
    RequirementCourseLink,
    category_status,
    compute_credits_summary,
    eligible_next_courses,
    eligible_next_courses_with_grades,
    find_double_counted_courses,
    flag_ambiguous_courses,
    format_missing_prereq_message,
    generate_regular_terms,
    grade_meets_minimum,
    missing_prereq_options,
    missing_prereqs_for_term,
    prereq_groups_for,
    prereq_groups_with_grades_for,
    prereqs_satisfied,
    prereqs_satisfied_for_term,
    prereqs_satisfied_with_grades,
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


def test_prereq_groups_for_returns_and_or_structure():
    groups = prereq_groups_for("CS 311", EDGES)
    assert ["CS 230", "CS 250"] in groups
    assert ["CS 220"] in groups
    assert prereq_groups_for("CS 121", EDGES) == []


def test_grade_meets_minimum():
    assert grade_meets_minimum("B+", "B") is True
    assert grade_meets_minimum("B", "B+") is False
    assert grade_meets_minimum("C", "C") is True
    assert grade_meets_minimum("C-", "C") is False
    # No grade on record defaults to meeting only the standard 'C' bar.
    assert grade_meets_minimum(None, "C") is True
    assert grade_meets_minimum(None, "B+") is False


def test_prereq_groups_with_grades_for_pairs_code_with_min_grade():
    edges = [
        PrereqEdge("CS 514", "CS 240", 0, min_grade="B+"),
        PrereqEdge("CS 514", "CS 311", 0, min_grade="B+"),
    ]
    groups = prereq_groups_with_grades_for("CS 514", edges)
    assert groups == [[("CS 240", "B+"), ("CS 311", "B+")]]


def test_prereqs_satisfied_with_grades_enforces_min_grade():
    edges = [PrereqEdge("CS 514", "CS 311", 0, min_grade="B+")]

    got_a_minus = {"CS 311": CourseFulfillment(status="completed", grade="A-")}
    assert prereqs_satisfied_with_grades("CS 514", got_a_minus, edges) is True

    got_b = {"CS 311": CourseFulfillment(status="completed", grade="B")}
    assert prereqs_satisfied_with_grades("CS 514", got_b, edges) is False

    # Skipped/credited courses have no grade to check — they fully satisfy.
    skipped = {"CS 311": CourseFulfillment(status="skipped")}
    assert prereqs_satisfied_with_grades("CS 514", skipped, edges) is True


def test_eligible_next_courses_with_grades_respects_min_grade():
    edges = [PrereqEdge("CS 514", "CS 311", 0, min_grade="B+")]
    all_codes = ["CS 311", "CS 514"]

    only_b = {"CS 311": CourseFulfillment(status="completed", grade="B")}
    assert "CS 514" not in eligible_next_courses_with_grades(all_codes, only_b, edges)

    got_b_plus = {"CS 311": CourseFulfillment(status="completed", grade="B+")}
    assert "CS 514" in eligible_next_courses_with_grades(all_codes, got_b_plus, edges)


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


def test_compute_credits_summary():
    courses_by_code = {
        "CS 121": Course("CS 121", "x", credits=4),
        "CS 187": Course("CS 187", "y", credits=4),
        "CS 230": Course("CS 230", "z", credits=3),
        "CS 311": Course("CS 311", "w", credits=3),
    }
    planned = [
        PlannedCourse("CS 121", term_position=0, status="completed"),
        PlannedCourse("CS 187", term_position=0, status="completed"),
        PlannedCourse("CS 230", term_position=1, status="planned"),
        PlannedCourse("CS 311", term_position=None, status="planned"),  # unscheduled backlog item
    ]
    summary = compute_credits_summary(120, 0, planned, courses_by_code)
    assert summary.scheduled_credits == 11  # everything with a term_position (121+187+230)
    assert summary.completed_credits == 8  # only the two completed courses
    assert summary.remaining_credits == 112  # 120 - 8


def test_compute_credits_summary_includes_incoming_and_credited_courses():
    courses_by_code = {
        "MATH 131": Course("MATH 131", "x", credits=4),
        "CS 121": Course("CS 121", "y", credits=4),
        "MATH 100": Course("MATH 100", "z", credits=3),  # skipped, shouldn't count
    }
    planned = [
        PlannedCourse("MATH 131", term_position=None, status="credited"),  # AP credit, never scheduled
        PlannedCourse("CS 121", term_position=0, status="completed"),
        PlannedCourse("MATH 100", term_position=None, status="skipped"),
    ]
    summary = compute_credits_summary(120, 8, planned, courses_by_code)  # 8 incoming AP credits
    assert summary.completed_credits == 16  # 8 incoming + 4 (MATH 131 credited) + 4 (CS 121 completed)
    assert summary.remaining_credits == 104


def test_compute_credits_summary_floors_remaining_at_zero():
    courses_by_code = {"CS 121": Course("CS 121", "x", credits=4)}
    planned = [PlannedCourse("CS 121", term_position=0, status="completed")]
    summary = compute_credits_summary(2, 0, planned, courses_by_code)  # already exceeds a tiny requirement
    assert summary.remaining_credits == 0


def test_prereqs_satisfied_for_term_requires_strictly_earlier_term():
    edges = [PrereqEdge("CS 230", "CS 187", 0)]
    planned_same_term = [
        PlannedCourse("CS 187", term_position=2, status="planned"),
    ]
    # CS 187 scheduled in the SAME term as CS 230 (position 2) doesn't satisfy it
    assert prereqs_satisfied_for_term("CS 230", 2, planned_same_term, edges) is False

    planned_earlier = [
        PlannedCourse("CS 187", term_position=1, status="planned"),
    ]
    assert prereqs_satisfied_for_term("CS 230", 2, planned_earlier, edges) is True


def test_prereqs_satisfied_for_term_via_skipped_or_credited_prereq():
    # Real case: student tested out of / got transfer credit for MATH 131 and
    # never put it on the calendar at all, but still needs to schedule MATH 132.
    edges = [PrereqEdge("MATH 132", "MATH 131", 0)]

    skipped = [PlannedCourse("MATH 131", term_position=None, status="skipped")]
    assert prereqs_satisfied_for_term("MATH 132", 0, skipped, edges) is True

    credited = [PlannedCourse("MATH 131", term_position=None, status="credited")]
    assert prereqs_satisfied_for_term("MATH 132", 0, credited, edges) is True

    missing = missing_prereqs_for_term("MATH 132", 0, skipped, edges)
    assert missing == []


def test_missing_prereqs_for_term_names_the_missing_course():
    edges = [PrereqEdge("CS 210", "CS 160", 0)]
    missing = missing_prereqs_for_term("CS 210", 1, [], edges)
    assert missing == [["CS 160"]]


def test_format_missing_prereq_message_single_path():
    msg = format_missing_prereq_message("CICS 210", [["CICS 160"]])
    assert msg == "You need to take CICS 160 in an earlier term before CICS 210."


def test_format_missing_prereq_message_and_group():
    msg = format_missing_prereq_message("COMPSCI 230", [["CICS 210", "COMPSCI 198C"]])
    assert "CICS 210 and COMPSCI 198C" in msg


def test_format_missing_prereq_message_or_of_and_groups():
    msg = format_missing_prereq_message("COMPSCI 311", [["CICS 210", "COMPSCI 250"], ["CICS 210", "MATH 455"]])
    assert "(CICS 210 and COMPSCI 250) or (CICS 210 and MATH 455)" in msg


def test_generate_regular_terms_alternates_fall_spring_by_year():
    terms = generate_regular_terms(6)
    assert [t["term_type"] for t in terms] == ["fall", "spring", "fall", "spring", "fall", "spring"]
    assert [t["position"] for t in terms] == [0, 1, 2, 3, 4, 5]
    assert terms[0]["label"] == "Year 1 - Fall"
    assert terms[2]["label"] == "Year 2 - Fall"
    assert terms[5]["label"] == "Year 3 - Spring"
