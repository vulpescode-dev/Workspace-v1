import { ArrowDown, ArrowUp, Copy, Plus, Trash2, X } from 'lucide-react'
import { useRef, type ReactNode } from 'react'

import { cn } from '@/lib/cn'

import { CHOICE_KINDS, GRID_KINDS, KIND_LABELS, type Choice, type Question, type QuestionKind } from '../api/forms.api'

const fieldClass = 'w-full rounded-xl border border-slate-200 bg-surface px-3 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm'
const KIND_GROUPS: { label: string; kinds: QuestionKind[] }[] = [
  { label: 'Texto', kinds: ['short_text', 'paragraph'] },
  { label: 'Opciones', kinds: ['single_choice', 'multiple_choice', 'dropdown'] },
  { label: 'Escalas', kinds: ['linear_scale', 'rating'] },
  { label: 'Cuadrículas', kinds: ['single_choice_grid', 'multiple_choice_grid'] },
  { label: 'Fecha y hora', kinds: ['date', 'time'] },
]

interface QuestionEditorProps {
  question: Question
  number: number
  total: number
  onChange: (question: Question) => void
  onMove: (delta: -1 | 1) => void
  onDuplicate: () => void
  onRemove: () => void
}

/** Una pregunta en el editor: texto, tipo y lo propio de su tipo (opciones, filas, escala…). */
export function QuestionEditor({ question, number, total, onChange, onMove, onDuplicate, onRemove }: QuestionEditorProps) {
  const set = (patch: Partial<Question>) => onChange({ ...question, ...patch })
  const isChoice = CHOICE_KINDS.includes(question.kind)
  const isGrid = GRID_KINDS.includes(question.kind)
  const locked = Boolean(question.has_answers)

  function changeKind(kind: QuestionKind) {
    const needsOptions = CHOICE_KINDS.includes(kind) || GRID_KINDS.includes(kind)
    set({
      kind,
      options: needsOptions ? (question.options.length ? question.options : [{ text: 'Opción 1' }]) : [],
      rows: GRID_KINDS.includes(kind) ? (question.rows.length ? question.rows : [{ text: 'Fila 1' }]) : [],
      has_other_option: kind === 'single_choice' || kind === 'multiple_choice' ? question.has_other_option : false,
      min_choices: kind === 'multiple_choice' ? question.min_choices : null,
      max_choices: kind === 'multiple_choice' ? question.max_choices : null,
      scale_min: kind === 'rating' ? 1 : question.scale_min,
    })
  }

  return (
    <div className="grid gap-4 rounded-2xl border border-slate-200/70 bg-surface p-4 shadow-sm shadow-slate-900/[0.03] sm:p-5">
      <div className="grid gap-3 sm:grid-cols-[1fr_220px]">
        <label className="grid gap-1">
          <span className="text-xs font-semibold text-slate-500">Pregunta {number}</span>
          <input value={question.title} onChange={(event) => set({ title: event.target.value })} maxLength={300} placeholder="Escribe la pregunta" className={cn(fieldClass, 'h-11 font-semibold')} />
        </label>
        <label className="grid gap-1">
          <span className="text-xs font-semibold text-slate-500">Tipo</span>
          <select value={question.kind} disabled={locked} onChange={(event) => changeKind(event.target.value as QuestionKind)} className={cn(fieldClass, 'h-11 disabled:opacity-60')}
            title={locked ? 'Ya tiene respuestas: no puede cambiar de tipo.' : undefined}>
            {KIND_GROUPS.map((group) => (
              <optgroup key={group.label} label={group.label}>{group.kinds.map((kind) => <option key={kind} value={kind}>{KIND_LABELS[kind]}</option>)}</optgroup>
            ))}
          </select>
        </label>
      </div>
      <input value={question.description} onChange={(event) => set({ description: event.target.value })} maxLength={500} placeholder="Ayuda (opcional)" aria-label="Ayuda"
        className={cn(fieldClass, 'h-10 text-slate-600')} />

      {isChoice && (
        <ChoiceList
          label="Opciones" items={question.options} onChange={(options) => set({ options })} marker={question.kind}
          extra={(question.kind === 'single_choice' || question.kind === 'multiple_choice') && (
            question.has_other_option
              ? <div className="flex items-center gap-2 pl-8 text-sm text-slate-500">Otro: <span className="flex-1 border-b border-dashed border-slate-300 italic">texto libre</span>
                  <button type="button" aria-label="Quitar «Otro»" onClick={() => set({ has_other_option: false })} className="grid size-8 place-items-center rounded-lg hover:bg-slate-100"><X className="size-4" aria-hidden /></button></div>
              : <button type="button" onClick={() => set({ has_other_option: true })} className="w-fit pl-8 text-sm font-semibold text-brand-600 hover:underline">Agregar «Otro»</button>
          )}
        />
      )}
      {isGrid && (
        <div className="grid gap-4 sm:grid-cols-2">
          <ChoiceList label="Filas" items={question.rows} onChange={(rows) => set({ rows })} marker="row" />
          <ChoiceList label="Columnas" items={question.options} onChange={(options) => set({ options })} marker={question.kind === 'single_choice_grid' ? 'single_choice' : 'multiple_choice'} />
        </div>
      )}
      {question.kind === 'multiple_choice' && (
        <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
          Elegir entre
          <NumberSelect value={question.min_choices} max={question.options.length + (question.has_other_option ? 1 : 0)} empty="sin mínimo" onChange={(min_choices) => set({ min_choices })} label="Mínimo de casillas" />
          y
          <NumberSelect value={question.max_choices} max={question.options.length + (question.has_other_option ? 1 : 0)} empty="sin máximo" onChange={(max_choices) => set({ max_choices })} label="Máximo de casillas" />
        </div>
      )}
      {(question.kind === 'linear_scale' || question.kind === 'rating') && (
        <div className="grid gap-3">
          <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
            {question.kind === 'linear_scale' ? (
              <>
                De
                <select value={question.scale_min} onChange={(event) => set({ scale_min: Number(event.target.value) })} aria-label="Inicio de la escala" className={cn(fieldClass, 'h-9 w-auto')}>
                  {[0, 1].map((n) => <option key={n} value={n}>{n}</option>)}
                </select>
                a
              </>
            ) : 'Estrellas:'}
            <select value={question.scale_max} onChange={(event) => set({ scale_max: Number(event.target.value) })} aria-label="Final de la escala" className={cn(fieldClass, 'h-9 w-auto')}>
              {Array.from({ length: 9 }, (_, i) => i + 2).map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          {question.kind === 'linear_scale' && (
            <div className="grid gap-2 sm:grid-cols-2">
              <input value={question.scale_min_label} onChange={(event) => set({ scale_min_label: event.target.value })} maxLength={100} placeholder={`Etiqueta del ${question.scale_min} (opcional)`} aria-label="Etiqueta del mínimo" className={cn(fieldClass, 'h-10')} />
              <input value={question.scale_max_label} onChange={(event) => set({ scale_max_label: event.target.value })} maxLength={100} placeholder={`Etiqueta del ${question.scale_max} (opcional)`} aria-label="Etiqueta del máximo" className={cn(fieldClass, 'h-10')} />
            </div>
          )}
        </div>
      )}
      {(question.kind === 'short_text' || question.kind === 'paragraph' || question.kind === 'date' || question.kind === 'time') && (
        <p className="rounded-xl border border-dashed border-slate-200 px-3 py-2.5 text-sm text-slate-400">{question.kind === 'short_text' ? 'Respuesta corta' : question.kind === 'paragraph' ? 'Respuesta larga' : question.kind === 'date' ? 'dd/mm/aaaa' : '--:--'}</p>
      )}

      <div className="flex flex-wrap items-center gap-1 border-t border-slate-100 pt-3">
        {isChoice && question.kind !== 'dropdown' && (
          <label className="mr-2 flex cursor-pointer items-center gap-2 text-sm text-slate-600 select-none">
            <input type="checkbox" checked={question.shuffle_options} onChange={(event) => set({ shuffle_options: event.target.checked })} className="size-4 accent-brand-500" /> Orden aleatorio
          </label>
        )}
        <label className="flex cursor-pointer items-center gap-2 text-sm font-semibold text-slate-700 select-none">
          <input type="checkbox" checked={question.is_required} onChange={(event) => set({ is_required: event.target.checked })} className="size-4 accent-brand-500" /> Obligatoria
        </label>
        <div className="ml-auto flex gap-0.5">
          <IconButton label="Subir" disabled={number === 1} onClick={() => onMove(-1)}><ArrowUp className="size-4" aria-hidden /></IconButton>
          <IconButton label="Bajar" disabled={number === total} onClick={() => onMove(1)}><ArrowDown className="size-4" aria-hidden /></IconButton>
          <IconButton label="Duplicar" onClick={onDuplicate}><Copy className="size-4" aria-hidden /></IconButton>
          <IconButton label="Eliminar pregunta" onClick={onRemove} danger><Trash2 className="size-4" aria-hidden /></IconButton>
        </div>
      </div>
      {locked && <p className="-mt-2 text-xs text-slate-500">Ya tiene respuestas: puedes corregir textos y opciones, pero no el tipo.</p>}
    </div>
  )
}

function IconButton({ label, onClick, disabled, danger, children }: { label: string; onClick: () => void; disabled?: boolean; danger?: boolean; children: ReactNode }) {
  return (
    <button type="button" aria-label={label} title={label} onClick={onClick} disabled={disabled}
      className={cn('pressable grid size-9 place-items-center rounded-lg text-slate-500 transition-colors duration-150 disabled:opacity-30', danger ? 'hover:bg-red-50 hover:text-red-600' : 'hover:bg-slate-100 hover:text-slate-800')}>
      {children}
    </button>
  )
}

function NumberSelect({ value, max, empty, onChange, label }: { value: number | null; max: number; empty: string; onChange: (value: number | null) => void; label: string }) {
  return (
    <select value={value ?? ''} onChange={(event) => onChange(event.target.value ? Number(event.target.value) : null)} aria-label={label} className={cn(fieldClass, 'h-9 w-auto')}>
      <option value="">{empty}</option>
      {Array.from({ length: Math.max(0, max) }, (_, i) => i + 1).map((n) => <option key={n} value={n}>{n}</option>)}
    </select>
  )
}

/** Lista editable de opciones (o filas/columnas). Enter en la última agrega otra. */
function ChoiceList({ label, items, onChange, marker, extra }: { label: string; items: Choice[]; onChange: (items: Choice[]) => void; marker: string; extra?: ReactNode }) {
  const list = useRef<HTMLUListElement>(null)
  const noun = label === 'Filas' ? 'Fila' : label === 'Columnas' ? 'Columna' : 'Opción'
  function add() {
    onChange([...items, { text: `${noun} ${items.length + 1}` }])
    requestAnimationFrame(() => list.current?.querySelector<HTMLInputElement>('li:last-child input')?.select())
  }
  return (
    <div className="grid gap-1.5">
      <span className="text-xs font-semibold text-slate-500">{label}</span>
      <ul ref={list} className="grid gap-1.5">
        {items.map((item, index) => (
          <li key={item.id ?? `new-${index}`} className="flex items-center gap-2">
            <span className={cn('size-4 shrink-0 border-2 border-slate-300', marker === 'multiple_choice' ? 'rounded' : marker === 'row' ? 'rounded-sm border-0 bg-slate-200' : marker === 'dropdown' ? 'border-0 text-center text-xs leading-4 font-semibold text-slate-400' : 'rounded-full')} aria-hidden>
              {marker === 'dropdown' && index + 1}
            </span>
            <input value={item.text} onChange={(event) => onChange(items.map((current, i) => (i === index ? { ...current, text: event.target.value } : current)))}
              onKeyDown={(event) => { if (event.key === 'Enter') { event.preventDefault(); if (index === items.length - 1) add() } }}
              maxLength={300} aria-label={`${noun} ${index + 1}`} className="h-9 min-w-0 flex-1 border-b border-transparent bg-transparent px-1 text-base hover:border-slate-200 focus:border-brand-500 focus:outline-none sm:text-sm" />
            <button type="button" aria-label={`Quitar ${noun.toLowerCase()} ${index + 1}`} disabled={items.length === 1}
              onClick={() => onChange(items.filter((_, i) => i !== index))} className="grid size-8 shrink-0 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 disabled:opacity-0">
              <X className="size-4" aria-hidden />
            </button>
          </li>
        ))}
      </ul>
      <button type="button" onClick={add} className="flex w-fit items-center gap-1.5 pl-6 text-sm font-semibold text-brand-600 hover:underline"><Plus className="size-4" aria-hidden /> Agregar {noun.toLowerCase()}</button>
      {extra}
    </div>
  )
}
