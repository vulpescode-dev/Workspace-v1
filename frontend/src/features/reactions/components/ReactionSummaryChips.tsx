import { useState } from 'react'

import { cn } from '@/lib/cn'

import { useEmojis } from '../hooks/useEmojis'
import type { ReactionSummary } from '../types'
import { AnimatedEmoji } from './AnimatedEmoji'

const MAX_CHIPS = 6

interface ReactionSummaryChipsProps {
  summary: ReactionSummary
  onToggle: (code: string) => void
  /** El emoji que acabo de elegir se anima una vez en su pastilla (confirmación). */
  celebrate?: { code: string; key: number } | null
  onShowAll?: () => void
}

/**
 * Pastillas compactas (20 px, estilo Discord): emoji + cuántos; la mía en azul. Tocar una pone esa
 * reacción o la quita si ya era la mía. Una pastilla nueva entra desde scale(.9) con fundido (200 ms).
 * El emoji que elijo se anima una vez en su pastilla; con mouse, la pastilla señalada se anima.
 */
export function ReactionSummaryChips({ summary, onToggle, celebrate, onShowAll }: ReactionSummaryChipsProps) {
  const { byCode } = useEmojis()
  const [hovered, setHovered] = useState<string | null>(null)
  if (!summary.total) return null
  const visible = summary.reactions.slice(0, MAX_CHIPS)
  const hidden = summary.reactions.slice(MAX_CHIPS).reduce((sum, reaction) => sum + reaction.count, 0)

  return (
    <ul className="flex flex-wrap items-center gap-1.5" aria-label={`${summary.total} reacciones`}>
      {visible.map(({ emoji: code, count }) => {
        const emoji = byCode.get(code)
        const isMine = code === summary.mine
        const party = celebrate?.code === code
        return (
          <li key={code} className="transition-[opacity,transform] duration-200 ease-out starting:scale-90 starting:opacity-0">
            <button
              type="button"
              onClick={() => onToggle(code)}
              onPointerEnter={(event) => event.pointerType === 'mouse' && setHovered(code)}
              onPointerLeave={() => setHovered(null)}
              aria-pressed={isMine}
              aria-label={`${emoji?.label ?? code}: ${count}${isMine ? ', tu reacción' : ''}`}
              className={cn(
                'pressable flex h-7 items-center gap-1 rounded-full border px-2 text-xs font-semibold tabular-nums transition-colors duration-150',
                isMine ? 'border-brand-200 bg-brand-50 text-brand-700' : 'border-slate-200 bg-surface text-slate-600 hover:bg-slate-50',
              )}
            >
              <AnimatedEmoji emoji={emoji} play={hovered === code ? 'loop' : party ? 'once' : false} replayKey={party ? celebrate.key : 0} className="size-5" />
              {count}
            </button>
          </li>
        )
      })}
      {hidden > 0 && <li className="px-1 text-xs font-semibold text-slate-500">+{hidden}</li>}
      {onShowAll && (
        <li>
          <button type="button" onClick={onShowAll} className="px-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800">
            Ver todo
          </button>
        </li>
      )}
    </ul>
  )
}
