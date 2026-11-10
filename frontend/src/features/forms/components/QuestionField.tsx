import { Star } from 'lucide-react'
import { useId, useState, type ReactNode } from 'react'

import { cn } from '@/lib/cn'

import type { AnswerInput, Choice, Question } from '../api/forms.api'

const inputClass = 'w-full rounded-xl border border-slate-200 bg-surface px-4 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm'

/** Orden aleatorio estable mientras la pregunta está en pantalla (Fisher–Yates). */
function useShuffled(items: Choice[], shuffle: boolean) {
  const [order] = useState(() => {
    const copy = [...items]
    if (shuffle) for (let i = copy.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [copy[i], copy[j]] = [copy[j], copy[i]] }
    return copy
  })
  return order
}

interface QuestionFieldProps {
  question: Question
  value: AnswerInput
  onChange: (value: AnswerInput) => void
  error?: string
}

/** Una pregunta lista para contestar: tarjeta con título, ayuda, el control según su tipo y su error. */
export function QuestionField({ question, value, onChange, error }: QuestionFieldProps) {
  const id = useId()
  const options = useShuffled(question.options, question.shuffle_options)
  const set = (patch: Partial<AnswerInput>) => onChange({ ...value, ...patch })
  const chosen = value.options ?? []
  const hint = question.kind === 'multiple_choice' && (question.min_choices || question.max_choices)
    ? question.min_choices && question.max_choices ? `Elige de ${question.min_choices} a ${question.max_choices}.` : question.min_choices ? `Elige al menos ${question.min_choices}.` : `Elige máximo ${question.max_choices}.`
    : ''

  let control: ReactNode = null
  switch (question.kind) {
    case 'short_text':
      control = <input id={id} value={value.text ?? ''} onChange={(event) => set({ text: event.target.value })} maxLength={500} placeholder="Tu respuesta" className={cn(inputClass, 'h-12')} aria-invalid={Boolean(error) || undefined} />
      break
    case 'paragraph':
      control = <textarea id={id} value={value.text ?? ''} onChange={(event) => set({ text: event.target.value })} maxLength={5000} rows={4} placeholder="Tu respuesta" className={cn(inputClass, 'resize-y py-3')} aria-invalid={Boolean(error) || undefined} />
      break
    case 'dropdown':
      control = (
        <select id={id} value={chosen[0] ?? ''} onChange={(event) => set({ options: event.target.value ? [Number(event.target.value)] : [] })} className={cn(inputClass, 'h-12 px-3')}>
          <option value="">Elige…</option>
          {options.map((option) => <option key={option.id} value={option.id}>{option.text}</option>)}
        </select>
      )
      break
    case 'single_choice':
    case 'multiple_choice': {
      const multiple = question.kind === 'multiple_choice'
      const otherOn = value.other !== undefined
      const toggle = (optionId: number) => set({ options: multiple ? (chosen.includes(optionId) ? chosen.filter((item) => item !== optionId) : [...chosen, optionId]) : [optionId], ...(!multiple && { other: undefined }) })
      control = (
        <div className="grid gap-1">
          {options.map((option) => (
            <ChoiceRow key={option.id} type={multiple ? 'checkbox' : 'radio'} name={id} checked={chosen.includes(option.id!)} onChange={() => toggle(option.id!)} label={option.text} />
          ))}
          {question.has_other_option && (
            <div className="flex items-center gap-1">
              <ChoiceRow type={multiple ? 'checkbox' : 'radio'} name={id} checked={otherOn}
                onChange={() => set(multiple ? { other: otherOn ? undefined : '' } : { other: '', options: [] })} label="Otro:" />
              <input value={value.other ?? ''} onChange={(event) => set({ other: event.target.value, ...(!multiple && { options: [] }) })} onFocus={() => !otherOn && set({ other: '', ...(!multiple && { options: [] }) })}
                maxLength={300} aria-label="Otro" className="h-9 min-w-0 flex-1 border-b border-slate-300 bg-transparent px-1 text-base focus:border-brand-500 focus:outline-none sm:text-sm" />
            </div>
          )}
        </div>
      )
      break
    }
    case 'linear_scale':
    case 'rating': {
      const low = question.kind === 'rating' ? 1 : question.scale_min
      const values = Array.from({ length: question.scale_max - low + 1 }, (_, index) => low + index)
      control = question.kind === 'rating' ? (
        <div className="flex flex-wrap gap-1" role="radiogroup" aria-labelledby={`${id}-title`}>
          {values.map((n) => (
            <button key={n} type="button" role="radio" aria-checked={value.number === n} aria-label={`${n} de ${question.scale_max}`} onClick={() => set({ number: value.number === n ? undefined : n })}
              className="pressable grid size-10 place-items-center rounded-lg hover:bg-amber-50">
              <Star className={cn('size-7 transition-colors duration-150', (value.number ?? 0) >= n ? 'fill-amber-400 text-amber-400' : 'text-slate-300')} aria-hidden />
            </button>
          ))}
        </div>
      ) : (
        <div className="grid gap-2">
          <div className="flex gap-1 overflow-x-auto pb-1" role="radiogroup" aria-labelledby={`${id}-title`}>
            {values.map((n) => (
              <button key={n} type="button" role="radio" aria-checked={value.number === n} onClick={() => set({ number: value.number === n ? undefined : n })}
                className={cn('pressable grid h-11 min-w-11 flex-1 place-items-center rounded-xl border text-sm font-semibold tabular-nums transition-colors duration-150', value.number === n ? 'border-brand-500 bg-brand-500 text-white' : 'border-slate-200 text-slate-700 hover:bg-slate-50')}>
                {n}
              </button>
            ))}
          </div>
          {(question.scale_min_label || question.scale_max_label) && (
            <div className="flex justify-between gap-4 text-xs text-slate-500"><span>{question.scale_min_label}</span><span className="text-right">{question.scale_max_label}</span></div>
          )}
        </div>
      )
      break
    }
    case 'single_choice_grid':
    case 'multiple_choice_grid': {
      const multiple = question.kind === 'multiple_choice_grid'
      const rows = value.rows ?? {}
      control = (
        <div className="-mx-1 overflow-x-auto px-1">
          <table className="w-full min-w-max border-separate border-spacing-y-1 text-sm">
            <thead>
              <tr><th className="w-1/3" />{question.options.map((column) => <th key={column.id} scope="col" className="px-2 pb-1 text-center text-xs font-medium text-slate-600">{column.text}</th>)}</tr>
            </thead>
            <tbody>
              {question.rows.map((row) => {
                const picked = rows[String(row.id)] ?? []
                return (
                  <tr key={row.id} className="bg-slate-50">
                    <th scope="row" className="rounded-l-lg px-3 py-2 text-left font-medium text-slate-700">{row.text}</th>
                    {question.options.map((column, index) => (
                      <td key={column.id} className={cn('px-2 py-2 text-center', index === question.options.length - 1 && 'rounded-r-lg')}>
                        <input type={multiple ? 'checkbox' : 'radio'} name={`${id}-${row.id}`} checked={picked.includes(column.id!)} aria-label={`${row.text}: ${column.text}`}
                          onChange={() => set({ rows: { ...rows, [String(row.id)]: multiple ? (picked.includes(column.id!) ? picked.filter((item) => item !== column.id) : [...picked, column.id!]) : [column.id!] } })}
                          className="size-5 accent-brand-500" />
                      </td>
                    ))}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )
      break
    }
    case 'date':
      control = <input id={id} type="date" value={value.date ?? ''} onChange={(event) => set({ date: event.target.value })} className={cn(inputClass, 'h-12 sm:w-56')} />
      break
    case 'time':
      control = <input id={id} type="time" value={value.time ?? ''} onChange={(event) => set({ time: event.target.value })} className={cn(inputClass, 'h-12 sm:w-40')} />
      break
  }

  return (
    <div className={cn('rounded-2xl border bg-surface p-5 shadow-sm shadow-slate-900/[0.03] transition-colors duration-150', error ? 'border-red-300' : 'border-slate-200/70')}>
      <label htmlFor={id} id={`${id}-title`} className="block text-base font-semibold text-slate-900">
        {question.title}{question.is_required && <span className="ml-1 text-red-500" aria-label="obligatoria">*</span>}
      </label>
      {(question.description || hint) && <p className="mt-1 text-sm text-slate-500">{[question.description, hint].filter(Boolean).join(' ')}</p>}
      <div className="mt-4">{control}</div>
      {error && <p className="mt-3 text-sm font-medium text-red-600" role="alert">{error}</p>}
    </div>
  )
}

function ChoiceRow({ type, name, checked, onChange, label }: { type: 'radio' | 'checkbox'; name: string; checked: boolean; onChange: () => void; label: string }) {
  return (
    <label className="flex min-h-11 cursor-pointer items-center gap-3 rounded-xl px-2 text-sm text-slate-800 transition-colors duration-150 hover:bg-slate-50">
      <input type={type} name={name} checked={checked} onChange={onChange} className="size-5 shrink-0 accent-brand-500" />
      {label}
    </label>
  )
}
