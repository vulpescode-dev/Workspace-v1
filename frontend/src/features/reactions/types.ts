import type { UserSummary } from '@/features/accounts/types'

/** Emoji del catálogo (`GET /api/catalogs/emojis/`). Los archivos son públicos (estáticos del backend). */
export interface Emoji {
  code: string
  char: string
  label: string
  svg_url: string
  lottie_url: string
  is_active: boolean
}

/** Resumen de reacciones de un post o comentario. `mine` = el código de mi reacción o `null`. */
export interface ReactionSummary {
  reactions: { emoji: string; count: number }[]
  total: number
  mine: string | null
}

/** Una fila de «Ver todo»: quién reaccionó y con qué. */
export interface ReactionEntry {
  user: UserSummary
  emoji: string
  updated_at: string
}
