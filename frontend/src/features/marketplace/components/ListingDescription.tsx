import { ChevronDown } from 'lucide-react'
import { useLayoutEffect, useRef, useState, type ReactNode } from 'react'

import { Card } from '@/components/ui/Card'
import { cn } from '@/lib/cn'

import { toBlocks, type Block } from '../utils/description'

/** Alto (px) a partir del cual la descripción se muestra recortada con «Leer descripción completa». */
const COLLAPSED_HEIGHT = 320

function renderBlock(block: Block, key: number): ReactNode {
  if (block.kind === 'h') return <h3 key={key} className="pt-1 text-sm font-bold text-slate-900">{block.text}</h3>
  if (block.kind === 'ul') {
    return (
      <ul key={key} className="grid gap-1.5">
        {block.items.map((item, index) => (
          <li key={index} className="flex gap-2.5">
            <span aria-hidden className="mt-[0.6em] size-1.5 shrink-0 rounded-full bg-brand-400" />
            <span className="min-w-0">{item}</span>
          </li>
        ))}
      </ul>
    )
  }
  return <p key={key} className="whitespace-pre-line">{block.text}</p>
}

/**
 * Descripción del anuncio en su propia tarjeta, a lo ancho de la columna principal (las descripciones
 * reales suelen ser largas y detalladas). Si pasa de cierto alto, se recorta con un degradado y un botón.
 */
export function ListingDescription({ text }: { text: string }) {
  const contentRef = useRef<HTMLDivElement>(null)
  const [overflows, setOverflows] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const blocks = toBlocks(text)

  useLayoutEffect(() => {
    const element = contentRef.current
    if (!element) return
    const measure = () => setOverflows(element.scrollHeight > COLLAPSED_HEIGHT + 48)   // margen: no recortar por 2 líneas
    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(element)
    return () => observer.disconnect()
  }, [text])

  const collapsed = overflows && !expanded
  return (
    <Card className="grid gap-4 p-5 lg:p-6">
      <h2 className="font-display text-lg font-bold text-slate-900">Descripción</h2>
      <div className="relative">
        <div
          ref={contentRef}
          className={cn('grid gap-3 text-[0.9375rem] leading-relaxed break-words text-slate-700', collapsed && 'overflow-hidden')}
          style={collapsed ? { maxHeight: COLLAPSED_HEIGHT } : undefined}
        >
          {blocks.map(renderBlock)}
        </div>
        {collapsed && <div aria-hidden className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-surface to-transparent" />}
      </div>
      {overflows && (
        <button
          type="button"
          onClick={() => setExpanded((value) => !value)}
          aria-expanded={expanded}
          className="pressable inline-flex w-fit items-center gap-1.5 rounded-lg text-sm font-semibold text-brand-600 hover:text-brand-700"
        >
          {expanded ? 'Mostrar menos' : 'Leer descripción completa'}
          <ChevronDown className={cn('size-4 transition-transform duration-200 ease-(--ease-out)', expanded && 'rotate-180')} aria-hidden />
        </button>
      )}
    </Card>
  )
}
