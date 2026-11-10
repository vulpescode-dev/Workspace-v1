import type { Person, Profile } from '@/features/accounts/types'
import { api } from '@/lib/api/client'
import type { Paginated } from '@/types/api'

export interface ProfilePhoto {
  id: number
  url: string
  width: number | null
  height: number | null
  /** Publicación a la que pertenece. */
  post: number
}

export const profileApi = {
  /** Sin `userId`: mi perfil. */
  get: (userId?: number) => api.get<Profile>(userId ? `/accounts/users/${userId}/` : '/accounts/me/').then(({ data }) => data),
  updateBio: (bio: string) => api.patch<Profile>('/accounts/me/', { bio }).then(({ data }) => data),
  uploadAvatar: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<Profile>('/accounts/me/avatar/', form).then(({ data }) => data)
  },
  removeAvatar: () => api.delete<Profile>('/accounts/me/avatar/').then(({ data }) => data),
  followers: (userId: number, page: number) =>
    api.get<Paginated<Person>>(`/social/users/${userId}/followers/`, { params: { page } }).then(({ data }) => data),
  following: (userId: number, page: number) =>
    api.get<Paginated<Person>>(`/social/users/${userId}/following/`, { params: { page } }).then(({ data }) => data),
  photos: (userId: number, page: number) =>
    api.get<Paginated<ProfilePhoto>>('/social/photos/', { params: { author: userId, page } }).then(({ data }) => data),
}

export const profileKeys = {
  all: ['profile'] as const,
  detail: (userId: number | 'me') => [...profileKeys.all, userId] as const,
  people: (userId: number, kind: 'followers' | 'following') => [...profileKeys.all, userId, kind] as const,
  photos: (userId: number) => [...profileKeys.all, userId, 'photos'] as const,
}
