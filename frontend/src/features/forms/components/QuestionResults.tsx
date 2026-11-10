import { Star } from 'lucide-react'
import { useState } from 'react'

import { cn } from '@/lib/cn'
import { formatRelative } from '@/lib/format'

import type { QuestionResult } from '../api/forms.api'

const pct = (count: number, total: number) => (total ? Math.round((count / total) * 100) : 0)

/**
 * Resumen de una pregunta. Una sola serie por gráfica (un tono de marca, sin leyenda): barras
 * horizontales con el conteo y el % escritos; la escala, columnas en orden con el promedio arriba; las
 * cuadrículas, una tabla con intensidad de un solo tono. Al pasar el mouse cada barra dice su valor completo.
 */
export function QuestionResults({ result }: { result: QuestionResult }) {
  const responses = result.responses
  return (
    <div className="grid gap-4 rounded-2xl border border-slate-200/70 bg-surface p-5 shadow-sm shadow-slate-900/[0.03]">
      <div>
        <h3 className="text-base font-semibold text-slate-900">{result.title}</h3>
        <p className="text-xs text-slate-500">{responses} {responses === 1 ? 'respuesta' : 'respuestas'}</p>
      </div>
      {responses === 0 ? <p className="text-sm text-slate-400">Aún no hay respuestas para esta pregunta.</p> : <Body result={result} />}
    </div>
  )
}

function Body({ result }: { result: QuestionResult }) {
  if (result.options) {
    // Casillas: cada persona puede elegir varias, el % es sobre quienes respondieron la pregunta.
    const bars = [...result.options.map((option) => ({ key: String(option.id), label: option.text + (option.archived ? ' (ya no está)' : ''), count: option.count }))]
    if (result.other?.length) bars.push({ key: 'other', label: 'Otro', count: result.other.length })
    return (
      <>
        <BarList bars={bars} total={result.responses} />
        {!!result.other?.length && <TextList title="Respuestas en «Otro»" items={result.other} />}
      </>
    )
  }
  if (result.distribution) {
    const max = Math.max(...result.distribution.map((item) => item.count), 1)
    const total = result.distribution.reduce((sum, item) => sum + item.count, 0)
    return (
      <div className="grid gap-3">
        <p className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-slate-900 tabular-nums">{result.average?.toLocaleString('es-MX')}</span>
          <span className="text-sm text-slate-500">promedio de {result.scale_max}</span>
          {result.kind === 'rating' && <Star className="size-5 fill-amber-400 text-amber-400" aria-hidden />}
        </p>
        <div className="flex h-36 items-end gap-1.5 border-b border-slate-200" role="img" aria-label={result.distribution.map((item) => `${item.value}: ${item.count}`).join(', ')}>
          {result.distribution.map((item) => (
            <div key={item.value} className="group relative flex h-full flex-1 flex-col justify-end" title={`${item.value}: ${item.count} ${item.count === 1 ? 'respuesta' : 'respuestas'} (${pct(item.count, total)} %)`}>
              {item.count > 0 && <span className="mb-1 text-center text-xs font-semibold text-slate-600 tabular-nums">{item.count}</span>}
              <div className="rounded-t-[4px] bg-brand-500 transition-[height,background-color] duration-300 ease-out group-hover:bg-brand-600" style={{ height: `${(item.count / max) * 100}%`, minHeight: item.count ? 4 : 0 }} />
            </div>
          ))}
        </div>
        <div className="flex gap-1.5 text-center text-xs text-slate-500 tabular-nums">{result.distribution.map((item) => <span key={item.value} className="flex-1">{item.value}</span>)}</div>
        {(result.scale_min_label || result.scale_max_label) && (
          <div className="flex justify-between text-xs text-slate-500"><span>{result.scale_min_label}</span><span>{result.scale_max_label}</span></div>
        )}
      </div>
    )
  }
  if (result.rows && result.columns) {
    const max = Math.max(...result.rows.flatMap((row) => row.counts), 1)
    return (
      <div className="-mx-1 overflow-x-auto px-1">
        <table className="w-full min-w-max border-separate border-spacing-0.5 text-sm">
          <thead><tr><th />{result.columns.map((column) => <th key={column.id} scope="col" className="px-2 pb-1 text-center text-xs font-medium text-slate-600">{column.text}</th>)}</tr></thead>
          <tbody>
            {result.rows.map((row) => (
              <tr key={row.id}>
                <th scope="row" className="pr-3 text-left font-medium text-slate-700">{row.text}</th>
                {row.counts.map((count, index) => {
                  const strength = count / max
                  return (
                    <td key={index} title={`${row.text} · ${result.columns![index].text}: ${count}`}
                      className={cn('h-10 min-w-14 rounded-md text-center font-semibold tabular-nums', !count && 'bg-slate-50 text-slate-400', strength > 0.55 ? 'text-white' : 'text-slate-700')}
                      style={count ? { backgroundColor: `color-mix(in oklab, var(--color-brand-600) ${Math.round(15 + strength * 85)}%, var(--color-surface))` } : undefined}>
                      {count || '–'}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }
  if (result.values) {
    return <BarList bars={result.values.map((item) => ({ key: item.value, label: result.kind === 'date' ? new Date(`${item.value}T00:00`).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' }) : item.value, count: item.count }))} total={result.responses} />
  }
  return <TextList items={result.texts ?? []} />
}

function BarList({ bars, total }: { bars: { key: string; label: string; count: number }[]; total: number }) {
  const max = Math.max(...bars.map((bar) => bar.count), 1)
  return (
    <ul className="grid gap-2.5">
      {bars.map((bar) => (
        <li key={bar.key} className="group grid gap-1" title={`${bar.label}: ${bar.count} ${bar.count === 1 ? 'respuesta' : 'respuestas'} (${pct(bar.count, total)} %)`}>
          <div className="flex items-baseline justify-between gap-3 text-sm">
            <span className="min-w-0 truncate text-slate-700">{bar.label}</span>
            <span className="shrink-0 text-slate-500 tabular-nums"><span className="font-semibold text-slate-800">{bar.count}</span> · {pct(bar.count, total)} %</span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full rounded-r-[4px] bg-brand-500 transition-[width,background-color] duration-300 ease-out group-hover:bg-brand-600" style={{ width: `${(bar.count / max) * 100}%` }} />
          </div>
        </li>
      ))}
    </ul>
  )
}

function TextList({ title, items }: { title?: string; items: { text: string; respondent: string; submitted_at: string }[] }) {
  const [all, setAll] = useState(false)
  const shown = all ? items : items.slice(0, 5)
  return (
    <div className="grid gap-2">
      {title && <p className="text-xs font-semibold text-slate-500">{title}</p>}
      <ul className="grid gap-2">
        {shown.map((item, index) => (
          <li key={index} className="rounded-xl bg-slate-50 px-3 py-2">
            <p className="text-sm break-words whitespace-pre-line text-slate-800">{item.text}</p>
            <p className="mt-1 text-xs text-slate-500">{item.respondent} · {formatRelative(item.submitted_at)}</p>
          </li>
        ))}
      </ul>
      {items.length > 5 && <button type="button" onClick={() => setAll(!all)} className="w-fit text-sm font-semibold text-brand-600 hover:underline">{all ? 'Ver menos' : `Ver las ${items.length}`}</button>}
    </div>
  )
}
