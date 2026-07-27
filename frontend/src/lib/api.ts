import { supabase } from './supabaseClient'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

async function authHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (!token) throw new Error('Not signed in')
  return { Authorization: `Bearer ${token}` }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = await authHeaders()
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...headers, ...(init?.headers ?? {}) },
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
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

export const api = {
  listCourses: () => request<Course[]>('/courses'),
  getPrereqTree: (code: string) => request<PrereqNode>(`/courses/${encodeURIComponent(code)}/prereq-tree`),
  listPrograms: () => request<DegreeProgram[]>('/programs'),
  getProgramStatus: (programId: string) => request<ProgramStatus>(`/programs/${programId}/status`),
  getCompleted: () => request<string[]>('/me/completed'),
  markCompleted: (course_code: string) =>
    request<void>('/me/completed', { method: 'POST', body: JSON.stringify({ course_code }) }),
  unmarkCompleted: (course_code: string) =>
    request<void>(`/me/completed/${encodeURIComponent(course_code)}`, { method: 'DELETE' }),
  getRecommendations: () => request<{ eligible_courses: Course[] }>('/me/recommendations'),
  chat: (message: string) =>
    request<{ reply: string }>('/agent/chat', { method: 'POST', body: JSON.stringify({ message }) }),
}
