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
            sort_order=row.get("sort_order", 0),
            description=row.get("description", ""),
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


# ---------------------------------------------------------------------------
# Semester planner
# ---------------------------------------------------------------------------


def fetch_plan_settings(user_id: str) -> dict | None:
    client = get_service_client()
    rows = client.table("user_plan_settings").select("*").eq("user_id", user_id).execute().data
    return rows[0] if rows else None


def upsert_plan_settings(user_id: str, incoming_credits: float, target_semesters: int) -> dict:
    client = get_service_client()
    result = (
        client.table("user_plan_settings")
        .upsert(
            {"user_id": user_id, "incoming_credits": incoming_credits, "target_semesters": target_semesters},
            on_conflict="user_id",
        )
        .execute()
    )
    return result.data[0]


def fetch_terms(user_id: str) -> list[dict]:
    client = get_service_client()
    return (
        client.table("user_terms")
        .select("*")
        .eq("user_id", user_id)
        .order("position")
        .execute()
        .data
    )


def insert_terms(user_id: str, terms: list[dict]) -> list[dict]:
    """terms: list of {term_type, label, position}. Used for first-time plan generation."""
    if not terms:
        return []
    client = get_service_client()
    rows = [{**t, "user_id": user_id} for t in terms]
    return client.table("user_terms").insert(rows).execute().data


def insert_term(user_id: str, term_type: str, label: str, position: int) -> dict:
    client = get_service_client()
    return (
        client.table("user_terms")
        .insert({"user_id": user_id, "term_type": term_type, "label": label, "position": position})
        .execute()
        .data[0]
    )


def shift_term_positions(user_id: str, from_position: int, delta: int) -> None:
    """
    Shifts every term at or after from_position by delta, to make room for an
    insertion (delta > 0) or close a gap (delta < 0). Applied highest-position
    first (delta > 0) or lowest-first (delta < 0) so the unique
    (user_id, position) constraint is never hit mid-shift.
    """
    client = get_service_client()
    rows = fetch_terms(user_id)
    affected = [r for r in rows if r["position"] >= from_position]
    affected.sort(key=lambda r: r["position"], reverse=delta > 0)
    for row in affected:
        client.table("user_terms").update({"position": row["position"] + delta}).eq("id", row["id"]).execute()


def delete_term(user_id: str, term_id: str) -> None:
    client = get_service_client()
    client.table("user_terms").delete().eq("user_id", user_id).eq("id", term_id).execute()


def fetch_planned_courses(user_id: str) -> list[dict]:
    client = get_service_client()
    return client.table("user_planned_courses").select("*").eq("user_id", user_id).execute().data


def fetch_planned_course(user_id: str, course_code: str) -> dict | None:
    client = get_service_client()
    rows = (
        client.table("user_planned_courses")
        .select("*")
        .eq("user_id", user_id)
        .eq("course_code", course_code)
        .execute()
        .data
    )
    return rows[0] if rows else None


def upsert_planned_course(
    user_id: str,
    course_code: str,
    term_id: str | None,
    status: str,
) -> dict:
    client = get_service_client()
    result = (
        client.table("user_planned_courses")
        .upsert(
            {
                "user_id": user_id,
                "course_code": course_code,
                "term_id": term_id,
                "status": status,
            },
            on_conflict="user_id,course_code",
        )
        .execute()
    )
    return result.data[0]


def delete_planned_course(user_id: str, course_code: str) -> None:
    client = get_service_client()
    client.table("user_planned_courses").delete().eq("user_id", user_id).eq(
        "course_code", course_code
    ).execute()
