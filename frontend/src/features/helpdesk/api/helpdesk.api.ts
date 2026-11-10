import type { UserSummary } from '@/features/accounts/types'
import { api } from '@/lib/api/client'
import type { Paginated } from '@/types/api'

export type TicketStatus = 'open' | 'in_progress' | 'waiting' | 'resolved' | 'closed'
export type TicketPriority = 'low' | 'normal' | 'high' | 'urgent'
export type TicketScope = 'mine' | 'assigned' | 'queue'

export const STATUS_LABELS: Record<TicketStatus, string> = {
  open: 'Abierto', in_progress: 'En proceso', waiting: 'En espera', resolved: 'Resuelto', closed: 'Cerrado',
}
export const PRIORITY_LABELS: Record<TicketPriority, string> = { low: 'Baja', normal: 'Normal', high: 'Alta', urgent: 'Urgente' }

interface Named { id: number; name: string }
export interface TicketCategory extends Named { kind: 'incident' | 'request'; description: string; department: Named }
export interface TicketAttachment { id: number; name: string; content_type: string; size: number; url: string; created_at: string }
export interface TicketComment { id: number; author: UserSummary; body: string; is_internal: boolean; attachments: TicketAttachment[]; created_at: string }
export interface TicketEvent {
  id: number
  kind: 'created' | 'status' | 'priority' | 'assignee' | 'category'
  actor: UserSummary
  old_value: string
  new_value: string
  old_label: string
  new_label: string
  created_at: string
}

/** Ticket en la lista (`GET /api/helpdesk/tickets/`). */
export interface Ticket {
  id: number
  folio: string
  title: string
  status: TicketStatus
  status_label: string
  priority: TicketPriority
  priority_label: string
  /** `null` = «Otro»: no estaba en la lista y nadie lo ha clasificado todavía. */
  category: { id: number; name: string; kind: TicketCategory['kind'] } | null
  /** `null` = sin clasificar: lo ven los agentes de todos los departamentos. */
  department: Named | null
  requester: UserSummary
  assignee: UserSummary | null
  created_at: string
  updated_at: string
  first_response_at: string | null
  resolved_at: string | null
  closed_at: string | null
}

/** Ticket completo: conversación (las notas internas solo llegan a agentes), archivos, historial y qué puedo hacer. */
export interface TicketDetail extends Ticket {
  description: string
  attachments: TicketAttachment[]
  comments: TicketComment[]
  events: TicketEvent[]
  permissions: { attend: boolean; comment: boolean; internal_notes: boolean; close: boolean; reopen: boolean }
}

export interface TicketFilters { scope?: TicketScope; status?: string; unassigned?: boolean; unclassified?: boolean; q?: string }
export type TicketChanges = Partial<{ status: TicketStatus; priority: TicketPriority; assignee: number | null; category: number }>

export const MAX_TICKET_FILES = 5

/** Texto para la categoría y el departamento de un ticket, también cuando es «Otro» sin clasificar. */
export const categoryLabel = (ticket: Pick<Ticket, 'category'>) => ticket.category?.name ?? 'Otro'
export const departmentLabel = (ticket: Pick<Ticket, 'department'>) => ticket.department?.name ?? 'Sin clasificar'

export const helpdeskApi = {
  me: () => api.get<{ all_departments: boolean; attends: Named[]; view_all: boolean }>('/helpdesk/me/').then(({ data }) => data),
  categories: () => api.get<TicketCategory[]>('/helpdesk/categories/').then(({ data }) => data),
  list: ({ scope, status, unassigned, unclassified, q }: TicketFilters, page: number) =>
    api.get<Paginated<Ticket>>('/helpdesk/tickets/', {
      params: { scope, status: status || undefined, unassigned: unassigned ? 1 : undefined, unclassified: unclassified ? 1 : undefined, q: q || undefined, page },
    }).then(({ data }) => data),
  get: (id: number) => api.get<TicketDetail>(`/helpdesk/tickets/${id}/`).then(({ data }) => data),
  /** Multipart: `category` (sin él = «Otro»), `title`, `description` y hasta 5 `files`. */
  create: (form: FormData) => api.post<TicketDetail>('/helpdesk/tickets/', form).then(({ data }) => data),
  /** Si al transferirlo dejas de verlo responde la forma corta con `visible: false`. */
  update: (id: number, changes: TicketChanges) =>
    api.patch<TicketDetail | (Ticket & { visible: false })>(`/helpdesk/tickets/${id}/`, changes).then(({ data }) => data),
  /** Multipart: `body`, `is_internal` y hasta 5 `files`. Responde el ticket completo. */
  comment: (id: number, form: FormData) => api.post<TicketDetail>(`/helpdesk/tickets/${id}/comments/`, form).then(({ data }) => data),
  agents: (id: number) => api.get<UserSummary[]>(`/helpdesk/tickets/${id}/agents/`).then(({ data }) => data),
}

export const helpdeskKeys = {
  all: ['helpdesk'] as const,
  me: () => [...helpdeskKeys.all, 'me'] as const,
  categories: () => [...helpdeskKeys.all, 'categories'] as const,
  lists: () => [...helpdeskKeys.all, 'list'] as const,
  list: (filters: TicketFilters) => [...helpdeskKeys.lists(), filters] as const,
  detail: (id: number) => [...helpdeskKeys.all, 'detail', id] as const,
  agents: (id: number) => [...helpdeskKeys.all, 'agents', id] as const,
}
