import { useCan } from '@/features/accounts/hooks/useCan'
import { SmilePlus } from 'lucide-react'
import { useState } from 'react'

import { cn } from '@/lib/cn'

import { ReactionSheet } from './ReactionSheet'

interface ReactionPickerProps {
  mine: string | null
  onPick: (code: string | null) => void
  disabled?: boolean
  /** Solo texto «Reaccionar», para la fila pequeña de un comentario. */
  compact?: boolean
  /** El botón está dentro de otra hoja (comentarios). */
  nested?: boolean
}

/** Botón «carita +» que abre la hoja de emojis animados (a todo el ancho, en cualquier pantalla). */
export function ReactionPicker({ mine, onPick, disabled, compact = false, nested = false }: ReactionPickerProps) {
  const canReact = useCan()('social.reactions.create')
  const [open, setOpen] = useState(false)
  // La hoja se crea al abrirla por primera vez (el feed tiene un botón por publicación) y luego se queda
  // montada para que Vaul anime también la salida.
  const [everOpened, setEverOpened] = useState(false)
  if (!canReact && !mine) return null   // sin permiso no se ofrece reaccionar (si ya reaccionó, puede quitarla)
  return (
    <>
      <button
        type="button"
        disabled={disabled}
        onClick={() => {
          setEverOpened(true)
          setOpen(true)
        }}
        aria-haspopup="dialog"
        aria-expanded={open}
        className={cn(
          compact
            ? 'rounded py-0.5 text-xs font-semibold hover:text-slate-800'
            : 'pressable flex h-9 items-center gap-2 rounded-xl px-3 text-sm font-semibold transition-colors duration-150',
          'disabled:opacity-60',
          mine ? 'text-brand-700' : compact ? 'text-slate-500' : 'text-slate-600 hover:bg-slate-100',
          mine && !compact && 'hover:bg-brand-50',
        )}
      >
        {!compact && <SmilePlus className="size-5" aria-hidden />}
        Reaccionar
      </button>
      {everOpened && <ReactionSheet open={open} onOpenChange={setOpen} mine={mine} onPick={onPick} nested={nested} />}
    </>
  )
}
