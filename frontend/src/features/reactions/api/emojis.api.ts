import { api } from '@/lib/api/client'

import type { Emoji } from '../types'

export const emojisApi = {
  list: () => api.get<Emoji[]>('/catalogs/emojis/').then(({ data }) => data),
}

export const emojiKeys = { all: ['catalogs', 'emojis'] as const }
