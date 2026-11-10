import { useState } from 'react'

const LONG_TEXT_CHARS = 420
const LONG_TEXT_LINES = 7

/** Texto con saltos de línea. Si es largo se corta con «Ver más» (sin animación: es lectura). */
export function PostBody({ text, expanded = false }: { text: string; expanded?: boolean }) {
  const isLong = text.length > LONG_TEXT_CHARS || text.split('\n').length > LONG_TEXT_LINES
  const [open, setOpen] = useState(expanded)
  const clamp = isLong && !open

  return (
    <div className="px-4 pt-3">
      <p className={`text-[15px] leading-relaxed break-words whitespace-pre-line text-slate-800 ${clamp ? 'line-clamp-6' : ''}`}>{text}</p>
      {clamp && (
        <button type="button" onClick={() => setOpen(true)} className="mt-1 text-sm font-semibold text-slate-500 hover:text-slate-800">
          Ver más
        </button>
      )}
    </div>
  )
}
