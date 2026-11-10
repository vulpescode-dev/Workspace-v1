import type { LucideIcon } from 'lucide-react'
import { useEffect, useRef, useState, type ReactNode } from 'react'

import { cn } from '@/lib/cn'

export interface MenuItem {
  label: string
  icon: LucideIcon
  onSelect: () => void
  danger?: boolean
}

interface MenuProps {
  /** Contenido del botón que abre el menú (p. ej. el ícono «…»). */
  trigger: ReactNode
  label: string
  items: MenuItem[]
  className?: string
}

/**
 * Menú pequeño anclado a un botón (opciones de una publicación, de un comentario…). Crece desde el
 * botón (origen arriba a la derecha) con opacidad + scale(.97) en 150 ms; se cierra con Escape,
 * clic fuera o al elegir.
 */
export function Menu({ trigger, label, items, className }: MenuProps) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onPointerDown = (event: PointerEvent) => !rootRef.current?.contains(event.target as Node) && setOpen(false)
    const onKeyDown = (event: KeyboardEvent) => event.key === 'Escape' && setOpen(false)
    document.addEventListener('pointerdown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('pointerdown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  return (
    <div ref={rootRef} className={cn('relative', className)}>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={label}
        className="pressable grid size-9 place-items-center rounded-full text-slate-500 transition-colors duration-150 hover:bg-slate-100 hover:text-slate-800"
      >
        {trigger}
      </button>
      <div
        role="menu"
        aria-label={label}
        className={cn(
          'absolute top-full right-0 z-20 mt-1 w-48 origin-top-right rounded-2xl border border-slate-200/70 bg-surface p-1.5 shadow-lg shadow-slate-900/10',
          'transition-[opacity,transform,visibility] duration-150 ease-out',
          open ? 'visible scale-100 opacity-100' : 'invisible scale-[.97] opacity-0',
        )}
      >
        {items.map((item) => (
          <button
            key={item.label}
            type="button"
            role="menuitem"
            tabIndex={open ? 0 : -1}
            onClick={() => {
              setOpen(false)
              item.onSelect()
            }}
            className={cn(
              'flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm font-medium',
              item.danger ? 'text-red-600 hover:bg-red-50' : 'text-slate-700 hover:bg-slate-100',
            )}
          >
            <item.icon className={cn('size-4', item.danger ? 'text-red-500' : 'text-slate-400')} aria-hidden />
            {item.label}
          </button>
        ))}
      </div>
    </div>
  )
}
