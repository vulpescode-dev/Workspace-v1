import type { UserSummary } from '@/features/accounts/types'
import type { ReactionSummary } from '@/features/reactions/types'

export type Audience = 'company' | 'followers'

export const AUDIENCE_LABELS: Record<Audience, string> = {
  company: 'Toda la empresa',
  followers: 'Solo seguidores',
}

export interface PostAttachment {
  id: number
  kind: 'image' | 'video'
  /** Vista autorizada de la API (nunca /media/). */
  url: string
  content_type: string
  size: number
  width: number | null
  height: number | null
}

/** `GET /api/social/posts/` */
export interface Post {
  id: number
  author: UserSummary
  body: string
  audience: Audience
  attachments: PostAttachment[]
  created_at: string
  edited_at: string | null
  reactions: ReactionSummary
  comments_count: number
  is_mine: boolean
}

export interface NewPost {
  body: string
  audience: Audience
  files: File[]
}
