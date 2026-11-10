import { MessagesSquare, RotateCw } from 'lucide-react'
import { useEffect, useRef } from 'react'

import { EmptyState } from '@/components/feedback/EmptyState'
import { SkeletonGroup } from '@/components/feedback/Skeleton'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Spinner } from '@/components/ui/Spinner'

import type { FeedFilters } from '../api/posts.api'
import { useFeed } from '../hooks/useFeed'
import { PostCard } from './PostCard'
import { PostCardSkeleton } from './PostCardSkeleton'

/**
 * Lista de publicaciones con scroll infinito: carga la siguiente página cuando el final queda a
 * ~600 px de verse. Estados: esqueletos (primera carga), error con «Reintentar», vacío y fin.
 */
export function PostFeed({ filters, emptyText = 'Cuando alguien publique algo aparecerá aquí.' }: { filters?: FeedFilters; emptyText?: string }) {
  const feed = useFeed(filters)
  const sentinelRef = useRef<HTMLDivElement>(null)
  const { hasNextPage, isFetchingNextPage, fetchNextPage } = feed

  useEffect(() => {
    const sentinel = sentinelRef.current
    if (!sentinel || !hasNextPage) return
    const observer = new IntersectionObserver(
      ([entry]) => entry.isIntersecting && !isFetchingNextPage && void fetchNextPage(),
      { rootMargin: '600px 0px' },
    )
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  if (feed.isPending) {
    return (
      <SkeletonGroup label="Cargando publicaciones" className="grid gap-4">
        <PostCardSkeleton />
        <PostCardSkeleton withMedia />
        <PostCardSkeleton />
      </SkeletonGroup>
    )
  }

  if (feed.isError) {
    return (
      <Card>
        <EmptyState
          icon={RotateCw}
          title="No se pudieron cargar las publicaciones"
          description="Revisa tu conexión e inténtalo de nuevo."
          action={<Button variant="outline" onClick={() => void feed.refetch()}>Reintentar</Button>}
        />
      </Card>
    )
  }

  const posts = feed.data.pages.flatMap((page) => page.results)
  if (!posts.length) {
    return (
      <Card>
        <EmptyState icon={MessagesSquare} title="Todavía no hay publicaciones" description={emptyText} />
      </Card>
    )
  }

  return (
    <div className="grid gap-4">
      {posts.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}
      <div ref={sentinelRef} aria-hidden />
      {isFetchingNextPage && (
        <div className="grid place-items-center py-4 text-brand-500">
          <Spinner label="Cargando más publicaciones" />
        </div>
      )}
      {feed.isFetchNextPageError && (
        <Button variant="outline" className="mx-auto" onClick={() => void fetchNextPage()}>
          No se pudo cargar más · Reintentar
        </Button>
      )}
      {!hasNextPage && posts.length > 3 && <p className="py-4 text-center text-sm text-slate-400">Ya viste todas las publicaciones.</p>}
    </div>
  )
}
