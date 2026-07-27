from pydantic import BaseModel


class CourseOut(BaseModel):
    code: str
    title: str
    description: str = ""
    credits: float = 3
    department: str = ""
    cross_listed_as: list[str] = []
    notes: str = ""


class PrereqNode(BaseModel):
    code: str
    title: str
    satisfied: bool
    missing_options: list[list[str]]  # each inner list is one "AND" path still missing; multiple = OR
    children: list["PrereqNode"] = []


PrereqNode.model_rebuild()


class CategoryStatusOut(BaseModel):
    category_id: str
    name: str
    required_courses: int | None
    required_credits: float | None
    completed_courses: list[str]
    satisfied: bool
    still_needed: int


class ProgramStatusOut(BaseModel):
    program_id: str
    program_name: str
    categories: list[CategoryStatusOut]
    double_counted_courses: dict[str, list[str]]
    ambiguous_courses: dict[str, str]


class CompletedCourseIn(BaseModel):
    course_code: str
    term: str | None = None
    grade: str | None = None


class RecommendationOut(BaseModel):
    eligible_courses: list[CourseOut]


class ChatMessageIn(BaseModel):
    message: str


class ChatMessageOut(BaseModel):
    reply: str
