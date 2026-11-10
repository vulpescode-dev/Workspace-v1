import type { FollowStats, Person } from '@/features/accounts/types'
import { api } from '@/lib/api/client'

export const followsApi = {
  suggestions: () => api.get<Person[]>('/social/follows/suggestions/').then(({ data }) => data),
  follow: (userId: number) => api.put<FollowStats>(`/social/follows/${userId}/`).then(({ data }) => data),
  unfollow: (userId: number) => api.delete<FollowStats>(`/social/follows/${userId}/`).then(({ data }) => data),
}

export const followsKeys = { all: ['follows'] as const, suggestions: () => [...followsKeys.all, 'suggestions'] as const }
