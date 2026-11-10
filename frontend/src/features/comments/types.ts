import type { UserSummary } from '@/features/accounts/types'
import type { ReactionSummary } from '@/features/reactions/types'

/**
 * Comentario o respuesta (`GET /api/social/posts/:id/comments/`). Un comentario raíz eliminado que
 * conserva respuestas llega con `is_deleted: true`, sin autor ni texto.
 */
export interface Comment {
  id: number
  parent: number | null
  author: UserSummary | null
  body: string
  created_at: string
  edited_at: string | null
  is_deleted: boolean
  is_mine: boolean
  /** Ausente donde los comentarios no llevan reacciones (blog). */
  reactions?: ReactionSummary
}

/** Comentario raíz con sus respuestas (un solo nivel). */
export interface CommentThread extends Comment {
  replies: Comment[]
}
