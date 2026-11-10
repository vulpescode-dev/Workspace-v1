import type { UserSummary } from '@/features/accounts/types'

export interface Story {
  id: number
  kind: 'image' | 'video'
  /** Vista autorizada de la API (nunca /media/). */
  url: string
  content_type: string
  width: number | null
  height: number | null
  created_at: string
  expires_at: string
  seen: boolean
  /** Cuántas personas lo vieron. Solo llega en MIS estados; en los ajenos es `null`. */
  views_count: number | null
}

/** Una persona en la fila de estados (`GET /api/social/stories/`). */
export interface StoryGroup {
  author: UserSummary
  is_mine: boolean
  has_unseen: boolean
  latest_at: string
  stories: Story[]
}

/** Una fila de «Visto por» (`GET /api/social/stories/:id/viewers/`). */
export interface StoryViewerEntry {
  user: UserSummary
  viewed_at: string
}
