import { Check, ChevronDown } from 'lucide-react'
import { useEffect, useId, useRef, useState, type ReactNode } from 'react'

import { cn } from '@/lib/cn'

import type { FieldControlProps } from './Field'

export interface ComboboxOption<T extends string | number> {
  value: T
  label: string
  /** Segunda línea gris (ayuda para elegir). También se busca en ella. */
  description?: string
  /** Encabezado del grupo. Las opciones del mismo grupo deben ir juntas. */
  group?: string
  icon?: ReactNode
  /** Siempre visible aunque no coincida con lo escrito (p. ej. «Otro»). */
  pinned?: boolean
}

interface ComboboxProps<T extends string | number> extends Partial<FieldControlProps> {
  options: ComboboxOption<T>[]
  value: T | null
  onChange: (value: T) => void
  placeholder?: string
  loading?: boolean
  emptyText?: string
}

const normalize = (text: string) => text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

/**
 * Select con búsqueda en un solo campo (como TomSelect): escribe para filtrar, ↑ ↓ para moverte, Enter
 * para elegir, Esc para cerrar solo la lista. Agrupa por `group` y busca en etiqueta, descripción y grupo,
 * sin importar acentos. Accesible: patrón combobox + listbox de ARIA.
 */
export function Combobox<T extends string | number>({
  options, value, onChange, placeholder = 'Elige una opción', loading = false, emptyText = 'Nada coincide.',
  id, invalid, 'aria-describedby': describedBy,
}: ComboboxProps<T>) {
  const listId = useId()
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLUListElement>(null)
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)

  const selected = options.find((option) => option.value === value)
  const term = normalize(query.trim())
  const visible = options.filter((option) =>
    option.pinned || !term || normalize(`${option.label} ${option.description ?? ''} ${option.group ?? ''}`).includes(term))
  const matches = visible.filter((option) => !option.pinned).length

  function show() {
    setOpen(true)
    setQuery('')
    setActive(Math.max(0, options.findIndex((option) => option.value === value)))
  }
  function choose(option: ComboboxOption<T>) {
    onChange(option.value)
    setOpen(false)
    setQuery('')
  }

  // Mantiene visible la opción activa al moverse con el teclado.
  useEffect(() => {
    if (open) listRef.current?.querySelector(`[data-index="${active}"]`)?.scrollIntoView({ block: 'nearest' })
  }, [active, open])

  // Esc cierra solo la lista. Radix escucha Esc en `document` (captura) y cerraría también la hoja:
  // `window` en captura llega antes.
  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== 'Escape' || event.target !== inputRef.current) return
      event.stopPropagation()
      setOpen(false)
      setQuery('')
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  }, [open])

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault()
      if (!open) return show()
      const step = event.key === 'ArrowDown' ? 1 : -1
      setActive((index) => (index + step + visible.length) % Math.max(visible.length, 1))
    } else if (event.key === 'Enter' && open) {
      event.preventDefault()   // no envía el formulario
      if (visible[active]) choose(visible[active])
    } else if (event.key === 'Tab') {
      setOpen(false)
      setQuery('')
    }
  }

  return (
    <div className="relative" onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) { setOpen(false); setQuery('') } }}>
      <input
        ref={inputRef}
        id={id}
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={open && visible[active] ? `${listId}-${active}` : undefined}
        aria-invalid={invalid || undefined}
        aria-describedby={describedBy}
        autoComplete="off"
        disabled={loading}
        value={open ? query : (selected?.label ?? '')}
        placeholder={loading ? 'Cargando…' : open && selected ? selected.label : placeholder}
        onChange={(event) => { setQuery(event.target.value); setActive(0); if (!open) setOpen(true) }}
        onFocus={show}
        onMouseDown={() => { if (!open && document.activeElement === inputRef.current) show() }}
        onKeyDown={onKeyDown}
        className={cn(
          'h-12 w-full rounded-xl border border-slate-200 bg-surface pr-10 pl-3 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none disabled:opacity-60 sm:text-sm',
          selected && !open && 'font-medium',
        )}
      />
      <ChevronDown aria-hidden className={cn('pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-slate-400 transition-transform duration-200 ease-(--ease-out)', open && 'rotate-180')} />

      {open && (
        <ul
          ref={listRef}
          id={listId}
          role="listbox"
          // Evita que el clic quite el foco del campo antes de elegir.
          onMouseDown={(event) => event.preventDefault()}
          className="absolute inset-x-0 top-full z-20 mt-1.5 max-h-72 origin-top animate-[combobox-in_150ms_var(--ease-out)] overflow-y-auto overscroll-contain rounded-xl border border-slate-200 bg-surface p-1 shadow-lg shadow-slate-900/10 [scrollbar-width:thin]"
        >
          {matches === 0 && term && <li className="px-3 py-2 text-sm text-slate-500" role="presentation">{emptyText}</li>}
          {visible.map((option, index) => {
            const header = option.group && option.group !== visible[index - 1]?.group
            const isActive = index === active
            const isSelected = option.value === value
            return (
              <li key={String(option.value)} role="presentation">
                {header && <p className="px-3 pt-2 pb-1 text-[0.6875rem] font-semibold tracking-wide text-slate-400 uppercase">{option.group}</p>}
                {option.pinned && index > 0 && !header && <hr className="mx-2 my-1 border-dashed border-slate-200" />}
                <div
                  id={`${listId}-${index}`}
                  data-index={index}
                  role="option"
                  aria-selected={isSelected}
                  onMouseMove={() => setActive(index)}
                  onClick={() => choose(option)}
                  className={cn('flex cursor-pointer items-start gap-2 rounded-lg px-3 py-2', isActive && 'bg-slate-100')}
                >
                  {option.icon && <span className="mt-0.5 text-slate-500">{option.icon}</span>}
                  <span className="min-w-0 flex-1">
                    <span className={cn('block text-sm', isSelected ? 'font-semibold text-brand-700' : 'font-medium text-slate-800')}>{option.label}</span>
                    {option.description && <span className="block truncate text-xs text-slate-500">{option.description}</span>}
                  </span>
                  {isSelected && <Check className="mt-0.5 size-4 shrink-0 text-brand-600" aria-hidden />}
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
