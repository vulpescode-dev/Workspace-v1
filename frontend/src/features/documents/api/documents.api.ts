import type { UserSummary } from '@/features/accounts/types'
import { api } from '@/lib/api/client'
import type { Paginated } from '@/types/api'

export type Visibility = 'public' | 'departments' | 'users'
export const VISIBILITY_LABELS: Record<Visibility, string> = { public: 'Toda la empresa', departments: 'Departamentos', users: 'Personas' }

export interface DocumentCategory { id: number; name: string; description: string }
export interface DocumentVersion {
  id: number
  number: number
  notes: string
  name: string
  content_type: string
  size: number
  uploaded_by: UserSummary
  created_at: string
  url: string
}
export interface DocumentItem {
  id: number
  title: string
  description: string
  category: DocumentCategory
  owner: UserSummary
  visibility: Visibility
  current_version: DocumentVersion | null
  created_at: string
  updated_at: string
}
export interface DocumentDetail extends DocumentItem {
  versions: DocumentVersion[]
  can_manage: boolean
  departments: { id: number; name: string }[] | null
  shared_with: UserSummary[] | null
}
export interface DocumentFilters { scope?: 'mine' | 'shared'; category?: number; q?: string }

export const documentsApi = {
  me: () => api.get<{ can_create: boolean; manage_all: boolean }>('/documents/me/').then(({ data }) => data),
  categories: () => api.get<DocumentCategory[]>('/documents/categories/').then(({ data }) => data),
  list: (filters: DocumentFilters, page: number) =>
    api.get<Paginated<DocumentItem>>('/documents/documents/', { params: { ...filters, q: filters.q || undefined, page } }).then(({ data }) => data),
  get: (id: number) => api.get<DocumentDetail>(`/documents/documents/${id}/`).then(({ data }) => data),
  create: (form: FormData) => api.post<DocumentDetail>('/documents/documents/', form).then(({ data }) => data),
  /** Solo lo que cambió. Si con el cambio dejas de verlo, responde `{ id, visible: false }`. */
  update: (id: number, changes: Record<string, unknown>) =>
    api.patch<DocumentDetail | { id: number; visible: false }>(`/documents/documents/${id}/`, changes).then(({ data }) => data),
  remove: (id: number) => api.delete(`/documents/documents/${id}/`),
  addVersion: (id: number, form: FormData) => api.post(`/documents/documents/${id}/versions/`, form),
  restore: (id: number, versionId: number) => api.post(`/documents/documents/${id}/versions/${versionId}/restore/`),
}

export const documentsKeys = {
  all: ['documents'] as const,
  me: () => [...documentsKeys.all, 'me'] as const,
  categories: () => [...documentsKeys.all, 'categories'] as const,
  lists: () => [...documentsKeys.all, 'list'] as const,
  list: (filters: DocumentFilters) => [...documentsKeys.lists(), filters] as const,
  detail: (id: number) => [...documentsKeys.all, 'detail', id] as const,
}
