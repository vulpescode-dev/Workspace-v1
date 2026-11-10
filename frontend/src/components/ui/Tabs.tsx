import type { KeyboardEvent } from 'react'

import { cn } from '@/lib/cn'

export interface TabOption<T extends string> {
  value: T
  label: string
}

interface TabsProps<T extends string> {
  label: string
  options: TabOption<T>[]
  value: T
  onChange: (value: T) => void
  className?: string
}

/**
 * Pestañas. Teléfono: píldoras (caben con el pulgar y se desplazan si no caben). Escritorio (≥ 1024 px):
 * subrayadas, como Facebook. Cambiar de pestaña no se anima (se hace muchas veces).
 * Teclado: flechas izquierda/derecha entre pestañas (patrón ARIA de tabs).
 */
export function Tabs<T extends string>({ label, options, value, onChange, className }: TabsProps<T>) {
  function onKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    const step = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0
    if (!step) return
    event.preventDefault()
    const next = options[(index + step + options.length) % options.length]
    onChange(next.value)
    ;(event.currentTarget.parentElement?.children[options.indexOf(next)] as HTMLElement | undefined)?.focus()
  }

  return (
    <div role="tablist" aria-label={label} className={cn('flex gap-2 overflow-x-auto [scrollbar-width:none] lg:gap-1 lg:border-b lg:border-slate-200', className)}>
      {options.map((option, index) => {
        const active = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={active}
            tabIndex={active ? 0 : -1}
            onClick={() => onChange(option.value)}
            onKeyDown={(event) => onKeyDown(event, index)}
            className={cn(
              'pressable shrink-0 text-sm font-semibold transition-colors duration-150',
              // Teléfono: píldoras
              'rounded-full px-4 py-2',
              active ? 'bg-brand-500 text-white' : 'bg-surface text-slate-600 hover:bg-slate-100',
              // Escritorio: subrayado
              'lg:-mb-px lg:rounded-none lg:border-b-2 lg:bg-transparent lg:px-4 lg:py-3 lg:hover:bg-transparent',
              active ? 'lg:border-brand-500 lg:text-brand-600' : 'lg:border-transparent lg:text-slate-500 lg:hover:text-slate-800',
            )}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
