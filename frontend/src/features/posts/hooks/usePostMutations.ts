import { useMutation, useQueryClient, type InfiniteData } from '@tanstack/react-query'
import { toast } from 'sonner'

import type { ReactionSummary } from '@/features/reactions/types'
import { getErrorMessage } from '@/lib/api/errors'
import type { Paginated } from '@/types/api'

import { postsApi } from '../api/posts.api'
import { postsKeys } from '../api/query-keys'
import type { Post } from '../types'

type FeedData = InfiniteData<Paginated<Post>>

/** Cambia una publicación en TODOS los feeds en caché (Inicio, perfiles…) y en su página de detalle, sin volver a pedirlos. */
export function usePatchPostInFeeds() {
  const queryClient = useQueryClient()
  return (postId: number, patch: (post: Post) => Post) => {
    queryClient.setQueriesData<FeedData>({ queryKey: postsKeys.feeds() }, (data) =>
      data && {
        ...data,
        pages: data.pages.map((page) => ({ ...page, results: page.results.map((post) => (post.id === postId ? patch(post) : post)) })),
      },
    )
    queryClient.setQueryData<Post>(postsKeys.detail(postId), (post) => post && patch(post))
  }
}

/** Publicar: al terminar, la publicación nueva aparece arriba del feed de Inicio. */
export function useCreatePost() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: postsApi.create,
    onSuccess: (post) => {
      queryClient.setQueryData<FeedData>(postsKeys.feed(), (data) =>
        data && { ...data, pages: data.pages.map((page, index) => (index === 0 ? { ...page, results: [post, ...page.results] } : page)) },
      )
      void queryClient.invalidateQueries({ queryKey: postsKeys.feeds(), refetchType: 'none' })
    },
  })
}

/** Calcula el resumen como quedará, para pintarlo al instante (actualización optimista). */
function applyReaction(summary: ReactionSummary, next: string | null): ReactionSummary {
  const counts = new Map(summary.reactions.map((reaction) => [reaction.emoji, reaction.count]))
  if (summary.mine) counts.set(summary.mine, (counts.get(summary.mine) ?? 1) - 1)
  if (next) counts.set(next, (counts.get(next) ?? 0) + 1)
  const reactions = [...counts].filter(([, count]) => count > 0).map(([emoji, count]) => ({ emoji, count }))
  return { reactions, total: reactions.reduce((sum, reaction) => sum + reaction.count, 0), mine: next }
}

/**
 * Las pastillas no se reordenan mientras las ves (no «saltan»): se conserva el orden que ya había,
 * se actualizan los números con los del servidor y las nuevas van al final.
 */
function keepOrder(current: ReactionSummary, server: ReactionSummary): ReactionSummary {
  const counts = new Map(server.reactions.map((reaction) => [reaction.emoji, reaction.count]))
  const kept = current.reactions.filter((reaction) => counts.has(reaction.emoji)).map((reaction) => ({ emoji: reaction.emoji, count: counts.get(reaction.emoji)! }))
  const added = server.reactions.filter((reaction) => !current.reactions.some((existing) => existing.emoji === reaction.emoji))
  return { ...server, reactions: [...kept, ...added] }
}

/**
 * Poner, cambiar o quitar mi reacción. La pantalla cambia al instante; si el servidor falla, se regresa
 * a como estaba y se avisa. La respuesta del servidor (resumen real) reemplaza al cálculo local.
 */
export function useReactToPost() {
  const patch = usePatchPostInFeeds()
  return useMutation({
    mutationFn: ({ post, emoji }: { post: Post; emoji: string | null }) =>
      emoji ? postsApi.react(post.id, emoji) : postsApi.unreact(post.id),
    onMutate: ({ post, emoji }) => {
      patch(post.id, (current) => ({ ...current, reactions: applyReaction(current.reactions, emoji) }))
      return { previous: post.reactions }
    },
    onError: (error, { post }, context) => {
      if (context) patch(post.id, (current) => ({ ...current, reactions: context.previous }))
      toast.error(getErrorMessage(error, 'No se pudo guardar tu reacción.'))
    },
    onSuccess: (summary, { post }) => patch(post.id, (current) => ({ ...current, reactions: keepOrder(current.reactions, summary) })),
  })
}

/** Editar texto y audiencia de mi publicación. La tarjeta se actualiza con lo que responde el servidor. */
export function useEditPost() {
  const patch = usePatchPostInFeeds()
  return useMutation({
    mutationFn: ({ postId, body, audience }: { postId: number; body: string; audience: Post['audience'] }) =>
      postsApi.edit(postId, { body, audience }),
    onSuccess: (post) => patch(post.id, (current) => ({ ...current, body: post.body, audience: post.audience, edited_at: post.edited_at })),
  })
}

/** Eliminar mi publicación: desaparece de todos los feeds en caché sin volver a pedirlos. */
export function useDeletePost() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (postId: number) => postsApi.remove(postId),
    onSuccess: (_, postId) => {
      queryClient.setQueriesData<FeedData>({ queryKey: postsKeys.feeds() }, (data) =>
        data && { ...data, pages: data.pages.map((page) => ({ ...page, results: page.results.filter((post) => post.id !== postId) })) },
      )
      queryClient.removeQueries({ queryKey: postsKeys.detail(postId) })
    },
  })
}
