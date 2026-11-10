import { useQuery } from '@tanstack/react-query'
import { Search, X } from 'lucide-react'
import { useState } from 'react'

import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import type { UserSummary } from '@/features/accounts/types'
import { peopleApi, peopleKeys } from '@/features/people/api/people.api'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { cn } from '@/lib/cn'

import { VISIBILITY_LABELS } from '../api/documents.api'
import type { Audience } from '../audience'

/**
 * «Quién lo ve»: toda la empresa, ciertos departamentos (chips) o ciertas personas (buscador del
 * directorio; las elegidas quedan como chips con su foto). Tú, como dueño(a), siempre lo ves.
 */
export function AudiencePicker({ value, onChange }: { value: Audience; onChange: (next: Audience) => void }) {
  const { visibility, departments, people } = value
  const [text, setText] = useState('')
  const search = useDebouncedValue(text.trim(), 300)
  const departmentList = useQuery({ queryKey: peopleKeys.departments(), queryFn: peopleApi.departments, enabled: visibility === 'departments', staleTime: 10 * 60_000 })
  const results = useQuery({
    queryKey: peopleKeys.directory({ search }),
    queryFn: () => peopleApi.directory({ search }, 1),
    enabled: visibility === 'users' && search.length > 0,
    placeholderData: (previous) => previous,
  })
  const chosen = new Set(people.map((person) => person.id))
  const matches = search ? (results.data?.results ?? []).filter((person) => !person.is_me && !chosen.has(person.id)).slice(0, 6) : []

  const toggleDepartment = (id: number) =>
    onChange({ ...value, departments: departments.includes(id) ? departments.filter((item) => item !== id) : [...departments, id] })
  const addPerson = (person: UserSummary) => {
    onChange({ ...value, people: [...people, { id: person.id, name: person.name, initials: person.initials, avatar_url: person.avatar_url }] })
    setText('')
  }

  return (
    <fieldset className="grid gap-2">
      <legend className="mb-1 text-sm font-semibold text-slate-700">Quién lo ve</legend>
      <div className="grid grid-cols-3 gap-2">
        {(['public', 'departments', 'users'] as const).map((option) => (
          <button
            key={option}
            type="button"
            aria-pressed={visibility === option}
            onClick={() => onChange({ ...value, visibility: option })}
            className={cn('pressable h-11 rounded-xl border px-1 text-sm leading-tight font-semibold transition-colors duration-150', visibility === option ? 'border-brand-500 bg-brand-50 text-brand-700' : 'border-slate-200 text-slate-600 hover:bg-slate-50')}
          >
            {VISIBILITY_LABELS[option]}
          </button>
        ))}
      </div>

      {visibility === 'departments' && (
        <div className="flex flex-wrap gap-2 pt-1">
          {departmentList.data?.map((item) => {
            const on = departments.includes(item.id)
            return (
              <button key={item.id} type="button" aria-pressed={on} onClick={() => toggleDepartment(item.id)}
                className={cn('pressable h-8 rounded-full px-3 text-sm font-medium transition-colors duration-150', on ? 'bg-brand-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200')}>
                {item.name}
              </button>
            )
          })}
        </div>
      )}

      {visibility === 'users' && (
        <div className="grid gap-2 pt-1">
          {people.length > 0 && (
            <ul className="flex flex-wrap gap-2" aria-label="Personas elegidas">
              {people.map((person) => (
                <li key={person.id} className="flex h-8 items-center gap-1.5 rounded-full bg-brand-50 pr-1 pl-1 text-sm font-medium text-brand-700">
                  <UserAvatar user={person} size="sm" />
                  <span className="max-w-40 truncate">{person.name}</span>
                  <button type="button" aria-label={`Quitar a ${person.name}`} onClick={() => onChange({ ...value, people: people.filter((item) => item.id !== person.id) })}
                    className="pressable grid size-6 place-items-center rounded-full hover:bg-brand-100">
                    <X className="size-3.5" aria-hidden />
                  </button>
                </li>
              ))}
            </ul>
          )}
          <label className="relative">
            <span className="sr-only">Buscar personas</span>
            <Search className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-slate-400" aria-hidden />
            <input
              type="search"
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="Busca por nombre, correo o área"
              className="h-11 w-full rounded-xl border border-slate-200 bg-surface pr-3 pl-10 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm"
            />
          </label>
          {search && (
            <ul className="grid gap-0.5 rounded-xl border border-slate-200 p-1">
              {matches.map((person) => (
                <li key={person.id}>
                  <button type="button" onClick={() => addPerson(person)} className="pressable flex w-full items-center gap-3 rounded-lg px-2 py-1.5 text-left hover:bg-slate-50">
                    <UserAvatar user={person} size="sm" />
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-semibold text-slate-900">{person.name}</span>
                      {(person.job_title || person.department) && <span className="block truncate text-xs text-slate-500">{[person.job_title, person.department].filter(Boolean).join(' · ')}</span>}
                    </span>
                  </button>
                </li>
              ))}
              {matches.length === 0 && <li className="px-2 py-2 text-sm text-slate-500">{results.isFetching ? 'Buscando…' : 'Nadie coincide con la búsqueda.'}</li>}
            </ul>
          )}
        </div>
      )}
    </fieldset>
  )
}
