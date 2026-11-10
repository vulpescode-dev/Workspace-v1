import { useState } from 'react'
import { toast } from 'sonner'

import { Card } from '@/components/ui/Card'
import { CommentsSheet } from '@/features/comments/components/CommentsSheet'
import { getErrorMessage } from '@/lib/api/errors'
import { cn } from '@/lib/cn'

import { useDeletePost, usePatchPostInFeeds } from '../hooks/usePostMutations'
import type { Post } from '../types'
import { PostActions } from './PostActions'
import { PostBody } from './PostBody'
import { PostEditor } from './PostEditor'
import { PostHeader } from './PostHeader'
import { PostMedia } from './PostMedia'

interface PostCardProps {
  post: Post
  /** Texto completo sin «Ver más» (página de detalle). */
  expanded?: boolean
  /** Abrir los comentarios al mostrarse (aviso «Nuevo comentario» → `/posts/:id?comments=1`). */
  openComments?: boolean
  /** Después de eliminarla (la página de detalle regresa al Inicio). */
  onDeleted?: () => void
  className?: string
}

/**
 * Tarjeta de publicación. ÚNICA para toda la app: Inicio, Perfil, Detalle del post y Búsqueda la usan
 * igual; las variaciones se piden con props (`expanded`), nunca copiando el componente.
 */
export function PostCard({ post, expanded = false, openComments = false, onDeleted, className }: PostCardProps) {
  const patch = usePatchPostInFeeds()
  // La hoja de comentarios se crea al abrirla la primera vez y se queda montada (Vaul anima la salida).
  const [comments, setComments] = useState<'never' | 'open' | 'closed'>(openComments ? 'open' : 'never')
  const [editing, setEditing] = useState(false)
  const remove = useDeletePost()

  function confirmDelete() {
    if (!window.confirm('¿Eliminar esta publicación? Se quitarán también sus comentarios y reacciones.')) return
    remove.mutate(post.id, {
      onSuccess: () => {
        toast('Publicación eliminada.')
        onDeleted?.()
      },
      onError: (error) => toast.error(getErrorMessage(error, 'No se pudo eliminar.')),
    })
  }

  return (
    <Card className={cn('overflow-visible transition-opacity duration-150', remove.isPending && 'opacity-50', className)}>
      <article aria-labelledby={`post-${post.id}-author`}>
        <PostHeader post={post} onEdit={() => setEditing(true)} onDelete={confirmDelete} />
        {editing ? <PostEditor post={post} onDone={() => setEditing(false)} /> : post.body && <PostBody text={post.body} expanded={expanded} />}
        {post.attachments.length > 0 && <PostMedia attachments={post.attachments} />}
        <PostActions post={post} onComment={() => setComments('open')} />
      </article>
      {comments !== 'never' && (
        <CommentsSheet
          postId={post.id}
          open={comments === 'open'}
          onOpenChange={(open) => setComments(open ? 'open' : 'closed')}
          onCountChange={(count) => patch(post.id, (current) => ({ ...current, comments_count: count }))}
        />
      )}
    </Card>
  )
}
