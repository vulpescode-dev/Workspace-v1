import { api } from '@/lib/api/client'
import type { ReactionEntry, ReactionSummary } from '@/features/reactions/types'
import type { Paginated } from '@/types/api'

import type { Audience, NewPost, Post } from '../types'

export interface FeedFilters {
  /** Solo las publicaciones de esta persona (perfil). */
  author?: number
}

export const postsApi = {
  list: (page: number, filters: FeedFilters = {}) =>
    api.get<Paginated<Post>>('/social/posts/', { params: { page, ...filters } }).then(({ data }) => data),

  get: (postId: number) => api.get<Post>(`/social/posts/${postId}/`).then(({ data }) => data),

  create: ({ body, audience, files }: NewPost) => {
    const form = new FormData()
    form.append('body', body)
    form.append('audience', audience)
    files.forEach((file) => form.append('files', file))
    return api.post<Post>('/social/posts/', form).then(({ data }) => data)
  },

  edit: (postId: number, changes: { body: string; audience: Audience }) =>
    api.patch<Post>(`/social/posts/${postId}/`, changes).then(({ data }) => data),

  remove: (postId: number) => api.delete(`/social/posts/${postId}/`),

  react: (postId: number, emoji: string) =>
    api.put<ReactionSummary>(`/social/posts/${postId}/reaction/`, { emoji }).then(({ data }) => data),

  reactions: (postId: number, page: number) =>
    api.get<Paginated<ReactionEntry>>(`/social/posts/${postId}/reactions/`, { params: { page } }).then(({ data }) => data),

  unreact: (postId: number) => api.delete<ReactionSummary>(`/social/posts/${postId}/reaction/`).then(({ data }) => data),
}
