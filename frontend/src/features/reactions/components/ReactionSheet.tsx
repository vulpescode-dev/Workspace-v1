import { Skeleton } from '@/components/feedback/Skeleton'
import { Sheet } from '@/components/ui/Sheet'
import { useInView } from '@/hooks/useInView'
import { cn } from '@/lib/cn'

import { useEmojis } from '../hooks/useEmojis'
import type { Emoji } from '../types'
import { AnimatedEmoji } from './AnimatedEmoji'

interface ReactionSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  mine: string | null
  onPick: (code: string | null) => void
  /** Se abre desde otra hoja (comentarios): Vaul la apila sobre ella en lugar de cerrarla. */
  nested?: boolean
}

/**
 * Todos los emojis animados: en el teléfono, hoja inferior a todo el ancho (se cierra arrastrando); en
 * escritorio, una ventana compacta al centro (antes era una franja de toda la pantalla). Al tocar uno, se
 * elige y se cierra. «Quitar» aparece si ya reaccionaste. Para no gastar batería, solo se animan los visibles.
 */
export function ReactionSheet({ open, onOpenChange, mine, onPick, nested = false }: ReactionSheetProps) {
  function pick(code: string | null) {
    onOpenChange(false)
    onPick(code)
  }

  return (
    <Sheet
      open={open}
      onOpenChange={onOpenChange}
      title="Reaccionar"
      size="lg"
      nested={nested}
      fullWidthOnPhone
      headerAction={mine && (
        <button type="button" onClick={() => pick(null)} className="pressable shrink-0 rounded-lg px-2 py-1 text-sm font-semibold text-red-600 hover:bg-red-50">
          Quitar mi reacción
        </button>
      )}
    >
      <div className="max-h-[60dvh] overflow-y-auto overscroll-contain px-3 pb-2 sm:px-4">
        <EmojiGrid mine={mine} onPick={pick} />
      </div>
    </Sheet>
  )
}

/**
 * Cuadrícula de emojis animados. Solo se animan los que están a la vista del contenedor con scroll.
 */
export function EmojiGrid({ mine, onPick }: { mine: string | null; onPick: (code: string) => void }) {
  const { active, isPending } = useEmojis()
  if (isPending) {
    return (
      <div className="grid grid-cols-[repeat(auto-fill,minmax(2.75rem,1fr))] gap-1" aria-hidden>
        {Array.from({ length: 28 }, (_, index) => <Skeleton key={index} className="mx-auto size-9 rounded-full" />)}
      </div>
    )
  }
  return (
    <ul className="grid grid-cols-[repeat(auto-fill,minmax(2.75rem,1fr))] gap-1">
      {active.map((emoji) => (
        <li key={emoji.code} className="grid place-items-center">
          <EmojiOption emoji={emoji} selected={emoji.code === mine} onPick={() => onPick(emoji.code)} />
        </li>
      ))}
    </ul>
  )
}

function EmojiOption({ emoji, selected, onPick }: { emoji: Emoji; selected: boolean; onPick: () => void }) {
  // Se anima mientras está a la vista; al salir de pantalla (desplazar la hoja) se detiene y libera memoria.
  const [ref, inView] = useInView<HTMLButtonElement>('40px')
  return (
    <button
      ref={ref}
      type="button"
      title={emoji.label}
      aria-label={emoji.label}
      aria-pressed={selected}
      onClick={onPick}
      className={cn(
        'pressable grid size-11 place-items-center rounded-2xl transition-colors duration-150 hover:bg-slate-100',
        selected && 'bg-brand-100 hover:bg-brand-100',
      )}
    >
      <AnimatedEmoji emoji={emoji} play={inView ? 'loop' : false} className="size-9" />
    </button>
  )
}
