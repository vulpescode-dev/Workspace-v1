import { useInfiniteQuery } from '@tanstack/react-query'

import { postsApi, type FeedFilters } from '../api/posts.api'
import { postsKeys } from '../api/query-keys'

/** Feed paginado (25 por página) para scroll infinito. El mismo hook sirve para Inicio y para el Perfil (`author`). */
export function useFeed(filters: FeedFilters = {}) {
  return useInfiniteQuery({
    queryKey: postsKeys.feed(filters),
    queryFn: ({ pageParam }) => postsApi.list(pageParam, filters),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page < last.total_pages ? last.page + 1 : undefined),
  })
}
