"""
Tool definitions + dispatch for the Claude agent. Every tool is scoped to a
single user_id supplied by the router (which got it from the verified JWT,
never from the LLM or the request body) so the model can never read or
reason about a different student's completed courses.

The model is only ever given the ability to CALL these read-only lookups —
it cannot write to the database, and it cannot invent an answer about
whether a requirement is satisfied without going through
requirement_engine's deterministic logic.
"""

from typing import Any

from app.services import catalog_repo
from app.services.requirement_engine import (
    eligible_next_courses,
    flag_ambiguous_courses,
    missing_prereq_options,
    prereqs_satisfied,
)

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "list_degree_programs",
        "description": "List every degree program (majors/minors) known to the system, with their ids and names.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_program_requirement_status",
        "description": (
            "Get the requirement breakdown for a degree program for the CURRENT user: "
            "each requirement category, whether it's satisfied, how many more courses are "
            "needed, which courses can double-count across categories, and which courses "
            "have cross-listing/ambiguity caveats that might affect whether they count."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "program_name": {
                    "type": "string",
                    "description": "Exact or approximate program name, e.g. 'BS Computer Science' or 'Business Minor'.",
                }
            },
            "required": ["program_name"],
        },
    },
    {
        "name": "check_course_prerequisites",
        "description": (
            "Check whether the CURRENT user has satisfied the prerequisites for a specific "
            "course, and if not, list exactly which course(s) are still missing (there may be "
            "multiple alternative paths, any ONE of which is sufficient)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"course_code": {"type": "string", "description": "e.g. 'CS 311'"}},
            "required": ["course_code"],
        },
    },
    {
        "name": "get_eligible_courses",
        "description": "List every course the CURRENT user is now eligible to take, given what they've already completed (Recommendation Mode).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "search_courses",
        "description": "Search the course catalog by keyword in the course code, title, or description. Use this when the user doesn't give an exact course code.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "check_course_ambiguity",
        "description": (
            "Check whether a specific course has any cross-listing or catalog-change caveats "
            "that might mean it doesn't count the way the user expects (e.g. 'this was "
            "cross-listed differently last year'). Always call this before telling a user a "
            "cross-listed or ambiguous-looking course definitely counts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"course_code": {"type": "string"}},
            "required": ["course_code"],
        },
    },
]


def dispatch_tool(tool_name: str, tool_input: dict[str, Any], user_id: str) -> Any:
    courses = catalog_repo.fetch_courses()
    courses_by_code = {c.code: c for c in courses}

    if tool_name == "list_degree_programs":
        return catalog_repo.fetch_programs()

    if tool_name == "get_program_requirement_status":
        program_name = tool_input["program_name"].strip().lower()
        programs = catalog_repo.fetch_programs()
        match = next((p for p in programs if p["name"].strip().lower() == program_name), None)
        if match is None:
            match = next((p for p in programs if program_name in p["name"].strip().lower()), None)
        if match is None:
            return {"error": f"No program matching '{tool_input['program_name']}' found."}

        from app.services.requirement_engine import category_status, find_double_counted_courses

        categories = catalog_repo.fetch_categories(program_id=match["id"])
        links = catalog_repo.fetch_requirement_links(category_ids=[c.id for c in categories])
        completed = catalog_repo.fetch_completed_course_codes(user_id)
        statuses = [category_status(cat, links, completed, courses_by_code) for cat in categories]
        relevant_codes = {link.course_code for link in links}
        return {
            "program": match["name"],
            "categories": [s.__dict__ for s in statuses],
            "double_counted_courses": find_double_counted_courses(links),
            "ambiguous_courses": flag_ambiguous_courses(
                [c for code, c in courses_by_code.items() if code in relevant_codes]
            ),
        }

    if tool_name == "check_course_prerequisites":
        code = tool_input["course_code"].strip().upper()
        edges = catalog_repo.fetch_prereq_edges()
        completed = catalog_repo.fetch_completed_course_codes(user_id)
        return {
            "course_code": code,
            "satisfied": prereqs_satisfied(code, completed, edges),
            "missing_options": missing_prereq_options(code, completed, edges),
        }

    if tool_name == "get_eligible_courses":
        edges = catalog_repo.fetch_prereq_edges()
        completed = catalog_repo.fetch_completed_course_codes(user_id)
        eligible = eligible_next_courses(list(courses_by_code.keys()), completed, edges)
        return {"eligible_courses": eligible}

    if tool_name == "search_courses":
        q = tool_input["query"].strip().lower()
        matches = [
            c
            for c in courses
            if q in c.code.lower() or q in c.title.lower() or q in c.description.lower()
        ]
        return {"matches": [{"code": c.code, "title": c.title} for c in matches[:15]]}

    if tool_name == "check_course_ambiguity":
        code = tool_input["course_code"].strip().upper()
        course = courses_by_code.get(code)
        if course is None:
            return {"error": f"Unknown course code '{code}'"}
        flags = flag_ambiguous_courses([course])
        return {"course_code": code, "note": flags.get(code, "No known ambiguity or cross-listing caveats.")}

    raise ValueError(f"Unknown tool: {tool_name}")
