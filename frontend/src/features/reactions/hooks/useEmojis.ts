import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'

import { emojiKeys, emojisApi } from '../api/emojis.api'
import type { Emoji } from '../types'

/** Catálogo de emojis: casi nunca cambia, se pide una vez por sesión. `byCode` sirve para pintar resúmenes. */
export function useEmojis() {
  const query = useQuery({ queryKey: emojiKeys.all, queryFn: emojisApi.list, staleTime: Infinity, gcTime: Infinity })
  const byCode = useMemo(() => new Map<string, Emoji>((query.data ?? []).map((emoji) => [emoji.code, emoji])), [query.data])
  const active = useMemo(() => (query.data ?? []).filter((emoji) => emoji.is_active), [query.data])
  return { ...query, byCode, active }
}
