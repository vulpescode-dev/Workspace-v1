import type { UserSummary } from '@/features/accounts/types'
import type { CommentSource } from '@/features/comments/api/comments.api'
import { commentsKeys } from '@/features/comments/api/comments.api'
import type { Comment, CommentThread } from '@/features/comments/types'
import type { ReactionEntry, ReactionSummary } from '@/features/reactions/types'
import { api } from '@/lib/api/client'
import type { Paginated } from '@/types/api'

export interface ArticleCategory { id: number; name: string; slug: string }

/** Tarjeta de la lista (`GET /api/blog/articles/`): sin el contenido. */
export interface Article {
  id: number
  slug: string
  title: string
  excerpt: string
  /** Pasa por la vista autorizada (se descarga con sesión). Vacío si no tiene portada. */
  cover_url: string
  category: ArticleCategory | null
  author: UserSummary
  status: 'draft' | 'published'
  published_at: string | null
  /** Publicado con fecha futura: solo lo ve quien lo escribió hasta que llegue. */
  is_scheduled: boolean
  created_at: string
  updated_at: string
  comments_count: number
  reactions: ReactionSummary
  is_mine: boolean
}

/** Artículo completo: `body` es HTML ya limpio por el servidor. */
export interface ArticleDetail extends Article { body: string }

export interface ArticleFilters { category?: string; q?: string; mine?: boolean }

export const blogApi = {
  permissions: () => api.get<{ can_write: boolean }>('/blog/permissions/').then(({ data }) => data),
  categories: () => api.get<ArticleCategory[]>('/blog/categories/').then(({ data }) => data),
  list: ({ category, q, mine }: ArticleFilters, page: number) =>
    api.get<Paginated<Article>>('/blog/articles/', { params: { category: category || undefined, q: q || undefined, mine: mine ? 1 : undefined, page } }).then(({ data }) => data),
  get: (id: number) => api.get<ArticleDetail>(`/blog/articles/${id}/`).then(({ data }) => data),
  /** Multipart (lleva `cover` si se eligió portada). */
  create: (form: FormData) => api.post<ArticleDetail>('/blog/articles/', form).then(({ data }) => data),
  update: (id: number, form: FormData) => api.patch<ArticleDetail>(`/blog/articles/${id}/`, form).then(({ data }) => data),
  remove: (id: number) => api.delete(`/blog/articles/${id}/`),
  react: (id: number, emoji: string) => api.put<ReactionSummary>(`/blog/articles/${id}/reaction/`, { emoji }).then(({ data }) => data),
  unreact: (id: number) => api.delete<ReactionSummary>(`/blog/articles/${id}/reaction/`).then(({ data }) => data),
  reactions: (id: number, page: number) =>
    api.get<Paginated<ReactionEntry>>(`/blog/articles/${id}/reactions/`, { params: { page } }).then(({ data }) => data),
}

export const blogKeys = {
  all: ['blog'] as const,
  permissions: () => [...blogKeys.all, 'permissions'] as const,
  categories: () => [...blogKeys.all, 'categories'] as const,
  lists: () => [...blogKeys.all, 'list'] as const,
  list: (filters: ArticleFilters) => [...blogKeys.lists(), filters] as const,
  detail: (id: number) => [...blogKeys.all, 'detail', id] as const,
  reactions: (id: number) => [...blogKeys.all, 'reactions', id] as const,
}

/** Comentarios de un artículo (sin reacciones por comentario). */
export const articleCommentSource = (articleId: number): CommentSource => ({
  key: commentsKeys.article(articleId),
  permission: 'blog.comments.create',
  list: (page) => api.get<Paginated<CommentThread>>(`/blog/articles/${articleId}/comments/`, { params: { page } }).then(({ data }) => data),
  create: (body, parent) =>
    api.post<Comment & { comments_count: number }>(`/blog/articles/${articleId}/comments/`, { body, parent }).then(({ data }) => data),
  edit: (commentId, body) => api.patch<Comment>(`/blog/comments/${commentId}/`, { body }).then(({ data }) => data),
  remove: (commentId) =>
    api.delete<{ comments_count: number; keep_placeholder: boolean }>(`/blog/comments/${commentId}/`).then(({ data }) => data),
})
