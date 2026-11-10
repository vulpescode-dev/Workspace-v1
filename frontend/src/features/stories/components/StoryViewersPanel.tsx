import { useInfiniteQuery } from '@tanstack/react-query'
import { Eye, X } from 'lucide-react'

import { ListSkeleton } from '@/components/feedback/ListSkeleton'
import { Button } from '@/components/ui/Button'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { formatRelative } from '@/lib/format'

import { storiesApi, storiesKeys } from '../api/stories.api'

/** «Visto por» de mi estado: panel que sube dentro del visor (el estado queda en pausa mientras está abierto). */
export function StoryViewersPanel({ storyId, count, onClose }: { storyId: number; count: number; onClose: () => void }) {
  const list = useInfiniteQuery({
    queryKey: storiesKeys.viewers(storyId),
    queryFn: ({ pageParam }) => storiesApi.viewers(storyId, pageParam),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page < last.total_pages ? last.page + 1 : undefined),
  })
  const people = list.data?.pages.flatMap((page) => page.results) ?? []

  return (
    <div
      role="dialog"
      aria-label="Visto por"
      className="absolute inset-x-0 bottom-0 z-30 flex max-h-[60%] flex-col rounded-t-3xl bg-surface pb-[env(safe-area-inset-bottom)] transition-transform duration-300 ease-[var(--ease-drawer)] starting:translate-y-full"
    >
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
        <p className="flex items-center gap-2 text-sm font-bold text-slate-900">
          <Eye className="size-4 text-slate-500" aria-hidden /> Visto por {count}
        </p>
        <button type="button" onClick={onClose} aria-label="Cerrar" className="pressable grid size-9 place-items-center rounded-full text-slate-500 hover:bg-slate-100">
          <X className="size-5" aria-hidden />
        </button>
      </div>
      <div className="overflow-y-auto overscroll-contain px-5 py-4">
        {list.isPending ? (
          <ListSkeleton rows={3} label="Cargando quién lo vio" />
        ) : people.length === 0 ? (
          <p className="py-4 text-center text-sm text-slate-500">Todavía nadie lo ha visto.</p>
        ) : (
          <ul className="grid gap-3">
            {people.map((entry) => (
              <li key={entry.user.id} className="flex items-center gap-3">
                <UserAvatar user={entry.user} />
                <span className="min-w-0 flex-1 truncate text-sm font-semibold text-slate-900">{entry.user.name}</span>
                <span className="text-xs text-slate-500">{formatRelative(entry.viewed_at)}</span>
              </li>
            ))}
          </ul>
        )}
        {list.hasNextPage && (
          <Button variant="ghost" size="sm" className="mt-3 w-full" loading={list.isFetchingNextPage} onClick={() => void list.fetchNextPage()}>
            Ver más
          </Button>
        )}
      </div>
    </div>
  )
}
