import { useQuery } from '@tanstack/react-query'
import { Cake, ChevronLeft, ChevronRight, Info } from 'lucide-react'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router'

import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { accountsApi } from '@/features/accounts/api/accounts.api'
import { accountsKeys } from '@/features/accounts/api/query-keys'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import type { Birthday } from '@/features/accounts/types'
import { addDays, dayKey, formatDayTitle, formatMonth, monthWeeks, parseDay } from '@/features/calendar/dates'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { cn } from '@/lib/cn'

const WEEKDAYS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

/**
 * /calendar — por ahora solo visual: la cuadrícula del mes y los cumpleaños que ya da la API del widget de
 * Inicio (`/api/accounts/birthdays/`: hoy y los próximos 30 días). Mes y día elegido van en la URL.
 * Pendiente (con autorización): cumpleaños de cualquier mes y eventos.
 */
export function CalendarPage() {
  useDocumentTitle('Calendario')
  const [params, setParams] = useSearchParams()
  const [today] = useState(() => new Date())
  const todayKey = dayKey(today)
  const monthParam = params.get('month')
  const month = monthParam && /^\d{4}-\d{2}$/.test(monthParam) ? parseDay(`${monthParam}-01`) : new Date(today.getFullYear(), today.getMonth(), 1)
  const isThisMonth = dayKey(month).slice(0, 7) === todayKey.slice(0, 7)
  const selected = params.get('day') ?? (isThisMonth ? todayKey : dayKey(month))

  const birthdays = useQuery({ queryKey: accountsKeys.birthdays(), queryFn: accountsApi.birthdays, staleTime: 10 * 60_000 })
  const byDay = new Map<string, Birthday[]>()
  for (const person of birthdays.data ?? []) {
    const key = dayKey(addDays(today, person.days_until))
    byDay.set(key, [...(byDay.get(key) ?? []), person])
  }

  function update(next: Record<string, string>) {
    const merged = new URLSearchParams(params)
    Object.entries(next).forEach(([key, value]) => (value ? merged.set(key, value) : merged.delete(key)))
    setParams(merged, { replace: true })
  }
  const go = (delta: number) => update({ month: dayKey(new Date(month.getFullYear(), month.getMonth() + delta, 1)).slice(0, 7), day: '' })
  const dayItems = byDay.get(selected) ?? []

  return (
    <>
      <PageHeader title="Calendario" description="Cumpleaños y fechas importantes de la empresa." />

      <Card className="mb-4 flex items-center gap-2 p-3">
        <Button variant="ghost" size="sm" aria-label="Mes anterior" onClick={() => go(-1)}><ChevronLeft className="size-5" aria-hidden /></Button>
        <Button variant="ghost" size="sm" aria-label="Mes siguiente" onClick={() => go(1)}><ChevronRight className="size-5" aria-hidden /></Button>
        <h2 className="min-w-0 flex-1 truncate text-lg font-bold text-slate-900">{formatMonth(month)}</h2>
        {!isThisMonth && <Button variant="outline" size="sm" onClick={() => update({ month: '', day: '' })}>Hoy</Button>}
      </Card>

      <div className="grid gap-4">
        <Card className="overflow-hidden">
          <div className="grid grid-cols-7 border-b border-slate-100 bg-slate-50 text-center text-xs font-semibold text-slate-500">
            {WEEKDAYS.map((name) => <div key={name} className="py-2">{name}</div>)}
          </div>
          <div className="grid grid-cols-7">
            {monthWeeks(month.getFullYear(), month.getMonth()).flat().map((date) => {
              const key = dayKey(date)
              const people = byDay.get(key) ?? []
              const outside = date.getMonth() !== month.getMonth()
              return (
                <button key={key} type="button" aria-pressed={selected === key} onClick={() => update({ day: key })}
                  aria-label={`${formatDayTitle(date)}${people.length ? `: cumpleaños de ${people.map((p) => p.name).join(', ')}` : ''}`}
                  className={cn('min-h-16 border-r border-b border-slate-100 p-1 text-left align-top transition-colors duration-150 sm:min-h-24 sm:p-1.5 [&:nth-child(7n)]:border-r-0',
                    outside ? 'bg-slate-50/60' : 'hover:bg-slate-50', selected === key && 'bg-brand-50/60 hover:bg-brand-50')}>
                  <span className={cn('mb-1 grid size-7 place-items-center rounded-full text-xs font-semibold tabular-nums', key === todayKey ? 'bg-brand-500 text-white' : outside ? 'text-slate-400' : 'text-slate-700')}>{date.getDate()}</span>
                  {people.length > 0 && (
                    <>
                      <Cake className="mx-1 size-4 text-pink-500 sm:hidden" aria-hidden />
                      <span className="hidden flex-col gap-0.5 sm:flex">
                        {people.slice(0, 2).map((person) => (
                          <span key={person.id} className="flex min-w-0 items-center gap-1 rounded-md bg-pink-50 px-1.5 py-0.5 text-[11px] leading-tight font-medium text-pink-800">
                            <Cake className="size-3 shrink-0" aria-hidden /><span className="truncate">{person.name.split(' ')[0]}</span>
                          </span>
                        ))}
                        {people.length > 2 && <span className="px-1.5 text-[11px] font-semibold text-slate-500">+{people.length - 2} más</span>}
                      </span>
                    </>
                  )}
                </button>
              )
            })}
          </div>
        </Card>

        <Card className="p-3">
          <h3 className="px-2 pt-1 pb-2 text-base font-bold text-slate-900">{formatDayTitle(parseDay(selected))}</h3>
          {dayItems.length === 0 ? (
            <p className="px-2 pb-2 text-sm text-slate-500">No hay nada este día.</p>
          ) : (
            <ul className="grid gap-0.5">
              {dayItems.map((person) => (
                <li key={person.id}>
                  <Link to={`/profile/${person.id}`} className="flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors duration-150 hover:bg-slate-50">
                    <UserAvatar user={person} size="sm" />
                    <span className="min-w-0 flex-1"><span className="block truncate text-sm font-semibold text-slate-900">Cumpleaños de {person.name}</span><span className="text-xs text-slate-500">{person.job_title || '¡Mándale una felicitación!'}</span></span>
                    <Cake className="size-5 shrink-0 text-pink-500" aria-hidden />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <p className="flex items-start gap-2 px-1 text-xs text-slate-500">
          <Info className="mt-px size-3.5 shrink-0" aria-hidden />
          Por ahora el calendario muestra los cumpleaños de los próximos 30 días. Los eventos y los cumpleaños de otros meses llegarán más adelante.
        </p>
      </div>
    </>
  )
}
