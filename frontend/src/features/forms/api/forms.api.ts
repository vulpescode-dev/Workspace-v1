import type { UserSummary } from '@/features/accounts/types'
import { api } from '@/lib/api/client'
import type { Paginated } from '@/types/api'

export type FormStatus = 'draft' | 'open' | 'closed'
export type QuestionKind =
  | 'short_text' | 'paragraph' | 'single_choice' | 'multiple_choice' | 'dropdown' | 'linear_scale' | 'rating'
  | 'single_choice_grid' | 'multiple_choice_grid' | 'date' | 'time'

export const KIND_LABELS: Record<QuestionKind, string> = {
  short_text: 'Respuesta corta', paragraph: 'Párrafo', single_choice: 'Opción única', multiple_choice: 'Casillas',
  dropdown: 'Desplegable', linear_scale: 'Escala lineal', rating: 'Calificación', single_choice_grid: 'Cuadrícula de opción única',
  multiple_choice_grid: 'Cuadrícula de casillas', date: 'Fecha', time: 'Hora',
}
export const CHOICE_KINDS: QuestionKind[] = ['single_choice', 'multiple_choice', 'dropdown']
export const GRID_KINDS: QuestionKind[] = ['single_choice_grid', 'multiple_choice_grid']
export const STATUS_LABELS: Record<FormStatus, string> = { draft: 'Borrador', open: 'Abierto', closed: 'Cerrado' }

export interface Choice { id?: number; text: string }
export interface Question {
  id?: number
  kind: QuestionKind
  title: string
  description: string
  is_required: boolean
  has_other_option: boolean
  shuffle_options: boolean
  min_choices: number | null
  max_choices: number | null
  scale_min: number
  scale_max: number
  scale_min_label: string
  scale_max_label: string
  options: Choice[]
  rows: Choice[]
  /** Solo para quien lo creó: ya tiene respuestas (no puede cambiar de tipo). */
  has_answers?: boolean | null
}

/** Tarjeta (`GET /api/forms/forms/`). `submissions_count` solo llega a quien lo creó. */
export interface FormSummary {
  uuid: string
  title: string
  description: string
  owner: UserSummary
  status: FormStatus
  opens_at: string | null
  closes_at: string | null
  one_submission_per_user: boolean
  accepting: boolean
  submitted: boolean
  questions_count: number
  submissions_count: number | null
  is_mine: boolean
  created_at: string
  updated_at: string
}
export interface FormDetail extends FormSummary { questions: Question[] }

/** Respuesta a una pregunta, como la espera `POST …/submissions/`. */
export interface AnswerInput {
  question: number
  text?: string
  options?: number[]
  other?: string
  number?: number
  date?: string
  time?: string
  rows?: Record<string, number[]>
}

interface Counted { id: number; text: string; archived: boolean; count: number }
export interface QuestionResult {
  id: number
  kind: QuestionKind
  title: string
  responses: number
  texts?: { text: string; respondent: string; submitted_at: string }[]
  options?: Counted[]
  other?: { text: string; respondent: string; submitted_at: string }[]
  scale_min?: number
  scale_max?: number
  scale_min_label?: string
  scale_max_label?: string
  distribution?: { value: number; count: number }[]
  average?: number | null
  columns?: Omit<Counted, 'count'>[]
  rows?: (Omit<Counted, 'count'> & { counts: number[] })[]
  values?: { value: string; count: number }[]
}
export interface FormResults { submissions_count: number; respondents_count: number; last_submitted_at: string | null; questions: QuestionResult[] }

export type FormScope = 'pending' | 'mine'
export type FormChanges = Partial<{ title: string; description: string; status: FormStatus; opens_at: string | null; closes_at: string | null; one_submission_per_user: boolean }>

export const formsApi = {
  me: () => api.get<{ can_create: boolean }>('/forms/me/').then(({ data }) => data),
  list: (scope: FormScope | undefined, q: string, page: number) =>
    api.get<Paginated<FormSummary>>('/forms/forms/', { params: { scope, q: q || undefined, page } }).then(({ data }) => data),
  get: (uuid: string) => api.get<FormDetail>(`/forms/forms/${uuid}/`).then(({ data }) => data),
  create: (title: string) => api.post<FormDetail>('/forms/forms/', { title }).then(({ data }) => data),
  update: (uuid: string, changes: FormChanges) => api.patch<FormDetail>(`/forms/forms/${uuid}/`, changes).then(({ data }) => data),
  saveQuestions: (uuid: string, questions: Question[]) => api.put<FormDetail>(`/forms/forms/${uuid}/questions/`, { questions }).then(({ data }) => data),
  remove: (uuid: string) => api.delete(`/forms/forms/${uuid}/`),
  submit: (uuid: string, answers: AnswerInput[]) => api.post(`/forms/forms/${uuid}/submissions/`, { answers }),
  results: (uuid: string) => api.get<FormResults>(`/forms/forms/${uuid}/results/`).then(({ data }) => data),
  csvUrl: (uuid: string) => `/api/forms/forms/${uuid}/results.csv`,
}

export const formsKeys = {
  all: ['forms'] as const,
  me: () => [...formsKeys.all, 'me'] as const,
  lists: () => [...formsKeys.all, 'list'] as const,
  list: (scope: FormScope | undefined, q: string) => [...formsKeys.lists(), scope ?? 'all', q] as const,
  detail: (uuid: string) => [...formsKeys.all, 'detail', uuid] as const,
  results: (uuid: string) => [...formsKeys.all, 'results', uuid] as const,
}

/** Pregunta nueva con valores por defecto para el editor. */
export function blankQuestion(kind: QuestionKind = 'single_choice'): Question {
  return {
    kind, title: '', description: '', is_required: false, has_other_option: false, shuffle_options: false,
    min_choices: null, max_choices: null, scale_min: 1, scale_max: 5, scale_min_label: '', scale_max_label: '',
    options: CHOICE_KINDS.includes(kind) || GRID_KINDS.includes(kind) ? [{ text: 'Opción 1' }] : [],
    rows: GRID_KINDS.includes(kind) ? [{ text: 'Fila 1' }] : [],
  }
}
