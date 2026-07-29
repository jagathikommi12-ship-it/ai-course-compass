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


class PrereqRefOut(BaseModel):
    code: str
    satisfied: bool  # has the user already completed this specific prereq course


class ChecklistCourseOut(BaseModel):
    code: str
    title: str
    credits: float
    satisfies_note: str = ""
    ambiguous_note: str = ""  # cross-listing/notes worth double-checking before assuming this counts
    status: str  # 'not_started' | 'planned' | 'completed'
    mandatory: bool  # required course vs. one option among an elective/choice category
    prereqs_met: bool
    prereq_groups: list[list[PrereqRefOut]] = []  # AND within a group, OR across groups


class ChecklistCategoryOut(BaseModel):
    category_id: str
    name: str
    description: str = ""
    required_courses: int | None
    required_credits: float | None
    courses: list[ChecklistCourseOut]
    completed_count: int
    total_count: int


class ProgramChecklistOut(BaseModel):
    program_id: str
    program_name: str
    categories: list[ChecklistCategoryOut]
    total_completed: int
    total_courses: int


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


# ---------------------------------------------------------------------------
# Semester planner
# ---------------------------------------------------------------------------


class PlanSettingsOut(BaseModel):
    incoming_credits: float
    target_semesters: int


class PlanSettingsIn(BaseModel):
    incoming_credits: float = 0


class TermOut(BaseModel):
    id: str
    term_type: str
    label: str
    position: int


class AddTermIn(BaseModel):
    term_type: str  # 'summer' | 'winter' (regular fall/spring terms come from plan settings generation)
    label: str
    after_position: int  # new term is inserted immediately after this position


class PlannedCourseOut(BaseModel):
    course_code: str
    title: str
    credits: float
    term_id: str | None
    status: str


class PlanCourseIn(BaseModel):
    course_code: str
    term_id: str | None = None
    status: str = "planned"


class CreditsSummaryOut(BaseModel):
    total_required: float
    scheduled_credits: float
    completed_credits: float
    remaining_credits: float


class PlanOut(BaseModel):
    settings: PlanSettingsOut | None
    terms: list[TermOut]
    planned_courses: list[PlannedCourseOut]
    credits_summary: CreditsSummaryOut
