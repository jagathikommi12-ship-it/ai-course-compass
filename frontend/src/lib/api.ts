import { supabase } from './supabaseClient'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

async function authHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (!token) throw new Error('Not signed in')
  return { Authorization: `Bearer ${token}` }
}

export class ApiError extends Error {
  status: number
  body: unknown
  constructor(status: number, statusText: string, body: unknown) {
    super(`${status} ${statusText}`)
    this.status = status
    this.body = body
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = await authHeaders()
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...headers, ...(init?.headers ?? {}) },
  })
  if (!res.ok) {
    let body: unknown = await res.text()
    try {
      body = JSON.parse(body as string)
    } catch {
      // leave as text
    }
    throw new ApiError(res.status, res.statusText, body)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export interface Course {
  code: string
  title: string
  description: string
  credits: number
  department: string
  cross_listed_as: string[]
  notes: string
}

export interface PrereqNode {
  code: string
  title: string
  satisfied: boolean
  missing_options: string[][]
  children: PrereqNode[]
}

export interface CategoryStatus {
  category_id: string
  name: string
  required_courses: number | null
  required_credits: number | null
  completed_courses: string[]
  satisfied: boolean
  still_needed: number
}

export interface ProgramStatus {
  program_id: string
  program_name: string
  categories: CategoryStatus[]
  double_counted_courses: Record<string, string[]>
  ambiguous_courses: Record<string, string>
}

export interface DegreeProgram {
  id: string
  name: string
  program_type: string
  description: string
}

export type CourseStatus = 'not_started' | 'planned' | 'completed' | 'skipped' | 'credited'

export interface PrereqRef {
  code: string
  satisfied: boolean
}

export interface ChecklistCourse {
  code: string
  title: string
  credits: number
  satisfies_note: string
  ambiguous_note: string
  status: CourseStatus
  mandatory: boolean
  prereqs_met: boolean
  prereq_groups: PrereqRef[][]
}

export interface ChecklistCategory {
  category_id: string
  name: string
  description: string
  required_courses: number | null
  required_credits: number | null
  courses: ChecklistCourse[]
  completed_count: number
  total_count: number
}

export interface ProgramChecklist {
  program_id: string
  program_name: string
  categories: ChecklistCategory[]
  total_completed: number
  total_courses: number
}

export interface PlanSettings {
  incoming_credits: number
}

export interface Term {
  id: string
  term_type: 'fall' | 'spring' | 'summer' | 'winter'
  label: string
  position: number
}

export interface PlannedCourse {
  course_code: string
  title: string
  credits: number
  term_id: string | null
  status: 'planned' | 'completed' | 'skipped' | 'credited'
}

export interface CreditsSummary {
  total_required: number
  scheduled_credits: number
  completed_credits: number
  remaining_credits: number
}

export interface Plan {
  settings: PlanSettings
  terms: Term[]
  planned_courses: PlannedCourse[]
  credits_summary: CreditsSummary
}

export interface PrereqViolation {
  message: string
  missing_options: string[][]
}

export const api = {
  listCourses: () => request<Course[]>('/courses'),
  getPrereqTree: (code: string) => request<PrereqNode>(`/courses/${encodeURIComponent(code)}/prereq-tree`),
  listPrograms: () => request<DegreeProgram[]>('/programs'),
  getProgramStatus: (programId: string) => request<ProgramStatus>(`/programs/${programId}/status`),
  getProgramChecklist: (programId: string) => request<ProgramChecklist>(`/programs/${programId}/checklist`),
  getCompleted: () => request<string[]>('/me/completed'),
  markCompleted: (course_code: string) =>
    request<void>('/me/completed', { method: 'POST', body: JSON.stringify({ course_code }) }),
  unmarkCompleted: (course_code: string) =>
    request<void>(`/me/completed/${encodeURIComponent(course_code)}`, { method: 'DELETE' }),
  getRecommendations: () => request<{ eligible_courses: Course[] }>('/me/recommendations'),
  chat: (message: string) =>
    request<{ reply: string }>('/agent/chat', { method: 'POST', body: JSON.stringify({ message }) }),

  getPlan: (programId?: string) => request<Plan>(`/me/plan${programId ? `?program_id=${programId}` : ''}`),
  updatePlanSettings: (settings: PlanSettings) =>
    request<PlanSettings>('/me/plan/settings', { method: 'PUT', body: JSON.stringify(settings) }),
  addTerm: (term_type: 'summer' | 'winter', label: string, after_position: number) =>
    request<Term>('/me/plan/terms', {
      method: 'POST',
      body: JSON.stringify({ term_type, label, after_position }),
    }),
  removeTerm: (termId: string) => request<void>(`/me/plan/terms/${termId}`, { method: 'DELETE' }),
  upsertPlanCourse: (body: { course_code: string; term_id?: string | null; status?: string }) =>
    request<PlannedCourse>('/me/plan/courses', { method: 'POST', body: JSON.stringify(body) }),
  removePlanCourse: (course_code: string) =>
    request<void>(`/me/plan/courses/${encodeURIComponent(course_code)}`, { method: 'DELETE' }),
}
