import type { UserSummary } from '@/features/accounts/types'
import { api } from '@/lib/api/client'
import type { Paginated } from '@/types/api'

/** Tarjeta del directorio (`GET /api/accounts/users/`). */
export interface DirectoryPerson extends UserSummary {
  email: string
  job_title: string
  department: string
  department_id: number | null
  is_me: boolean
  is_following: boolean
}

export interface Department {
  id: number
  name: string
  description: string
  parent_id: number | null
  head: UserSummary | null
  members_count: number
}

/** Nodo del organigrama (`GET /api/org/chart/`): por jefe directo. */
export interface ChartNode extends UserSummary {
  job_title: string
  department: { id: number; name: string } | null
  reports_count: number
  children: ChartNode[]
}

export interface DirectoryFilters {
  search?: string
  department?: number
}

export const peopleApi = {
  directory: ({ search, department }: DirectoryFilters, page: number) =>
    api.get<Paginated<DirectoryPerson>>('/accounts/users/', { params: { search: search || undefined, department, page } }).then(({ data }) => data),
  departments: () => api.get<Department[]>('/org/departments/').then(({ data }) => data),
  chart: (depth = 10) =>
    api.get<{ depth: number; unassigned_count: number; roots: ChartNode[] }>('/org/chart/', { params: { depth } }).then(({ data }) => data),
}

export const peopleKeys = {
  all: ['people'] as const,
  directory: (filters: DirectoryFilters) => [...peopleKeys.all, 'directory', filters] as const,
  departments: () => [...peopleKeys.all, 'departments'] as const,
  chart: () => [...peopleKeys.all, 'chart'] as const,
}
