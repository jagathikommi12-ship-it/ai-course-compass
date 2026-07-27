"""
Data access layer between Supabase and the pure-python requirement_engine
dataclasses. Uses the service_role client for read efficiency (the catalog
tables are public-read anyway), but every per-user read/write in this file
takes an explicit user_id argument and filters on it in the query — the
caller (routers) must always pass the user_id that came from the verified
JWT (see app/auth.py), never one taken from a request body/query param.
"""

from app.services.requirement_engine import (
    Course,
    PrereqEdge,
    RequirementCategory,
    RequirementCourseLink,
)
from app.supabase_client import get_service_client


def fetch_courses() -> list[Course]:
    client = get_service_client()
    rows = client.table("courses").select("*").execute().data
    return [
        Course(
            code=row["code"],
            title=row["title"],
            description=row.get("description", ""),
            credits=row.get("credits", 3),
            department=row.get("department", ""),
            cross_listed_as=tuple(row.get("cross_listed_as") or ()),
            notes=row.get("notes", ""),
        )
        for row in rows
    ]


def fetch_prereq_edges() -> list[PrereqEdge]:
    client = get_service_client()
    rows = client.table("course_prerequisites").select("*").execute().data
    return [
        PrereqEdge(
            course_code=row["course_code"],
            prereq_code=row["prereq_code"],
            group_id=row.get("group_id", 0),
        )
        for row in rows
    ]


def fetch_programs() -> list[dict]:
    client = get_service_client()
    return client.table("degree_programs").select("*").execute().data


def fetch_categories(program_id: str | None = None) -> list[RequirementCategory]:
    client = get_service_client()
    query = client.table("requirement_categories").select("*")
    if program_id:
        query = query.eq("program_id", program_id)
    rows = query.execute().data
    return [
        RequirementCategory(
            id=row["id"],
            program_id=row["program_id"],
            name=row["name"],
            min_courses=row.get("min_courses"),
            min_credits=row.get("min_credits"),
        )
        for row in rows
    ]


def fetch_requirement_links(category_ids: list[str] | None = None) -> list[RequirementCourseLink]:
    client = get_service_client()
    query = client.table("requirement_courses").select("*")
    if category_ids is not None:
        query = query.in_("category_id", category_ids)
    rows = query.execute().data
    return [
        RequirementCourseLink(
            category_id=row["category_id"],
            course_code=row["course_code"],
            satisfies_note=row.get("satisfies_note", ""),
        )
        for row in rows
    ]


def fetch_completed_course_codes(user_id: str) -> set[str]:
    client = get_service_client()
    rows = (
        client.table("user_completed_courses")
        .select("course_code")
        .eq("user_id", user_id)
        .execute()
        .data
    )
    return {row["course_code"] for row in rows}


def add_completed_course(user_id: str, course_code: str, term: str | None, grade: str | None) -> None:
    client = get_service_client()
    client.table("user_completed_courses").upsert(
        {"user_id": user_id, "course_code": course_code, "term": term, "grade": grade},
        on_conflict="user_id,course_code",
    ).execute()


def remove_completed_course(user_id: str, course_code: str) -> None:
    client = get_service_client()
    client.table("user_completed_courses").delete().eq("user_id", user_id).eq(
        "course_code", course_code
    ).execute()
