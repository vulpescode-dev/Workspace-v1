import { useInfiniteQuery } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'

import { ListSkeleton } from '@/components/feedback/ListSkeleton'
import { Button } from '@/components/ui/Button'
import { Sheet } from '@/components/ui/Sheet'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { cn } from '@/lib/cn'
import type { Paginated } from '@/types/api'

import { useEmojis } from '../hooks/useEmojis'
import type { ReactionEntry, ReactionSummary } from '../types'
import { EmojiIcon } from './EmojiIcon'

interface ReactionListSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  summary: ReactionSummary
  /** Llave de caché y función para pedir una página de «quién reaccionó» (posts, comentarios, blog…). */
  queryKey: readonly unknown[]
  fetchPage: (page: number) => Promise<Paginated<ReactionEntry>>
}

/** «Ver todo»: resumen por emoji (filtro) y la lista de quién reaccionó con qué. */
export function ReactionListSheet({ open, onOpenChange, summary, queryKey, fetchPage }: ReactionListSheetProps) {
  const { byCode } = useEmojis()
  const [filter, setFilter] = useState<string | null>(null)
  const list = useInfiniteQuery({
    queryKey,
    queryFn: ({ pageParam }) => fetchPage(pageParam),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page < last.total_pages ? last.page + 1 : undefined),
    enabled: open,
  })
  const people = (list.data?.pages.flatMap((page) => page.results) ?? []).filter((entry) => !filter || entry.emoji === filter)

  return (
    <Sheet open={open} onOpenChange={onOpenChange} title="Reacciones" tall>

      <div className="flex gap-1.5 overflow-x-auto px-5 py-3 [scrollbar-width:none]">
        <FilterChip active={filter === null} onClick={() => setFilter(null)}>
          Todas · {summary.total}
        </FilterChip>
        {summary.reactions.map(({ emoji: code, count }) => (
          <FilterChip key={code} active={filter === code} onClick={() => setFilter(code)}>
            <EmojiIcon emoji={byCode.get(code)} className="size-4" /> {count}
          </FilterChip>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto overscroll-contain px-5 pb-5">
        {list.isPending ? (
          <ListSkeleton rows={5} label="Cargando reacciones" />
        ) : list.isError ? (
          <p className="py-6 text-center text-sm text-slate-500">No se pudo cargar la lista.</p>
        ) : (
          <ul className="grid gap-3">
            {people.map((entry) => (
              <li key={`${entry.user.id}-${entry.emoji}`} className="flex items-center gap-3">
                <UserAvatar user={entry.user} />
                <span className="min-w-0 flex-1 truncate text-sm font-semibold text-slate-900">{entry.user.name}</span>
                <EmojiIcon emoji={byCode.get(entry.emoji)} className="size-6" />
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
    </Sheet>
  )
}

function FilterChip({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        'pressable flex h-8 shrink-0 items-center gap-1 rounded-full border px-3 text-xs font-semibold tabular-nums transition-colors duration-150',
        active ? 'border-brand-500 bg-brand-500 text-white' : 'border-slate-200 text-slate-600 hover:bg-slate-50',
      )}
    >
      {children}
    </button>
  )
}
