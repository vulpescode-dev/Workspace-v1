import type { FeedFilters } from './posts.api'

export const postsKeys = {
  all: ['posts'] as const,
  feeds: () => [...postsKeys.all, 'feed'] as const,
  feed: (filters: FeedFilters = {}) => [...postsKeys.feeds(), filters] as const,
  detail: (postId: number) => [...postsKeys.all, 'detail', postId] as const,
  reactions: (postId: number) => [...postsKeys.all, postId, 'reactions'] as const,
}
