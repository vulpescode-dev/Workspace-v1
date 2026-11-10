import { useInfiniteQuery, useMutation, useQueryClient, type InfiniteData } from '@tanstack/react-query'
import { toast } from 'sonner'

import type { ReactionSummary } from '@/features/reactions/types'
import { getErrorMessage } from '@/lib/api/errors'
import type { Paginated } from '@/types/api'

import type { CommentSource } from '../api/comments.api'
import type { Comment, CommentThread } from '../types'

type ThreadsData = InfiniteData<Paginated<CommentThread>>

/** Hilos de comentarios de una publicación o artículo (más antiguos primero), paginados. */
export function useComments(source: CommentSource, enabled: boolean) {
  return useInfiniteQuery({
    queryKey: source.key,
    queryFn: ({ pageParam }) => source.list(pageParam),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page < last.total_pages ? last.page + 1 : undefined),
    enabled,
  })
}

/**
 * Publicar, editar, borrar y reaccionar. Tras escribir se vuelve a pedir la lista (el servidor decide el
 * orden y los «Comentario eliminado»); `onCountChange` actualiza el contador de la tarjeta (post o artículo).
 */
export function useCommentMutations(source: CommentSource, onCountChange: (count: number) => void) {
  const queryClient = useQueryClient()
  const key = source.key
  const refresh = () => queryClient.invalidateQueries({ queryKey: key })
  const fail = (fallback: string) => (error: unknown) => toast.error(getErrorMessage(error, fallback))

  const patchComment = (commentId: number, patch: (comment: Comment) => Comment) =>
    queryClient.setQueryData<ThreadsData>(key, (data) =>
      data && {
        ...data,
        pages: data.pages.map((page) => ({
          ...page,
          results: page.results.map((thread) => ({
            ...(thread.id === commentId ? (patch(thread) as CommentThread) : thread),
            replies: thread.replies.map((reply) => (reply.id === commentId ? patch(reply) : reply)),
          })),
        })),
      },
    )

  const create = useMutation({
    mutationFn: ({ body, parent }: { body: string; parent: number | null }) => source.create(body, parent),
    onSuccess: async (comment) => {
      onCountChange(comment.comments_count)
      await refresh()
    },
    onError: fail('No se pudo publicar el comentario.'),
  })

  const edit = useMutation({
    mutationFn: ({ id, body }: { id: number; body: string }) => source.edit(id, body),
    onSuccess: (comment) => patchComment(comment.id, (current) => ({ ...current, body: comment.body, edited_at: comment.edited_at })),
    onError: fail('No se pudo guardar el cambio.'),
  })

  const remove = useMutation({
    mutationFn: (id: number) => source.remove(id),
    onSuccess: async ({ comments_count }) => {
      onCountChange(comments_count)
      await refresh()
    },
    onError: fail('No se pudo eliminar el comentario.'),
  })

  const react = useMutation({
    mutationFn: ({ id, emoji }: { id: number; emoji: string | null }) => source.react!(id, emoji),
    onSuccess: (summary: ReactionSummary, { id }) => patchComment(id, (current) => ({ ...current, reactions: summary })),
    onError: fail('No se pudo guardar tu reacción.'),
  })

  return { create, edit, remove, react }
}
