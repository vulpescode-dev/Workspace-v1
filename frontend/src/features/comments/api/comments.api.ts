import type { ReactionSummary } from '@/features/reactions/types'
import { api } from '@/lib/api/client'
import type { Paginated } from '@/types/api'

import type { Comment, CommentThread } from '../types'

export const commentsApi = {
  list: (postId: number, page: number) =>
    api.get<Paginated<CommentThread>>(`/social/posts/${postId}/comments/`, { params: { page } }).then(({ data }) => data),
  create: (postId: number, body: string, parent: number | null) =>
    api.post<Comment & { comments_count: number }>(`/social/posts/${postId}/comments/`, { body, parent }).then(({ data }) => data),
  edit: (commentId: number, body: string) => api.patch<Comment>(`/social/comments/${commentId}/`, { body }).then(({ data }) => data),
  remove: (commentId: number) =>
    api.delete<{ comments_count: number; keep_placeholder: boolean }>(`/social/comments/${commentId}/`).then(({ data }) => data),
  react: (commentId: number, emoji: string) =>
    api.put<ReactionSummary>(`/social/comments/${commentId}/reaction/`, { emoji }).then(({ data }) => data),
  unreact: (commentId: number) => api.delete<ReactionSummary>(`/social/comments/${commentId}/reaction/`).then(({ data }) => data),
}

export const commentsKeys = {
  all: ['comments'] as const,
  post: (postId: number) => [...commentsKeys.all, postId] as const,
  article: (articleId: number) => [...commentsKeys.all, 'article', articleId] as const,
}

/**
 * De dónde salen los comentarios (una publicación, un artículo del blog…). Los componentes y hooks de
 * comentarios solo hablan con esta interfaz. `react` es opcional: en el blog los comentarios no llevan reacciones.
 */
export interface CommentSource {
  key: readonly unknown[]
  /** Permiso para comentar o responder aquí (`useCan`). */
  permission: string
  list: (page: number) => Promise<Paginated<CommentThread>>
  create: (body: string, parent: number | null) => Promise<Comment & { comments_count: number }>
  edit: (commentId: number, body: string) => Promise<Comment>
  remove: (commentId: number) => Promise<{ comments_count: number; keep_placeholder: boolean }>
  react?: (commentId: number, emoji: string | null) => Promise<ReactionSummary>
}

/** Comentarios de una publicación del muro. */
export const postCommentSource = (postId: number): CommentSource => ({
  key: commentsKeys.post(postId),
  permission: 'social.comments.create',
  list: (page) => commentsApi.list(postId, page),
  create: (body, parent) => commentsApi.create(postId, body, parent),
  edit: commentsApi.edit,
  remove: commentsApi.remove,
  react: (commentId, emoji) => (emoji ? commentsApi.react(commentId, emoji) : commentsApi.unreact(commentId)),
})
