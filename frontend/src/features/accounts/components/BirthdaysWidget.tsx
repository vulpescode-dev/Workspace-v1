import { useQuery } from '@tanstack/react-query'
import { Cake } from 'lucide-react'

import { ListSkeleton } from '@/components/feedback/ListSkeleton'
import { Widget } from '@/components/ui/Widget'

import { accountsApi } from '../api/accounts.api'
import { accountsKeys } from '../api/query-keys'
import { UserAvatar } from './UserAvatar'

const monthDay = new Intl.DateTimeFormat('es-MX', { day: 'numeric', month: 'long', timeZone: 'UTC' })

/** Cumpleaños de hoy y de los próximos 30 días (nunca el año). Si no hay, el widget no se muestra. */
export function BirthdaysWidget() {
  const { data, isPending, isError } = useQuery({ queryKey: accountsKeys.birthdays(), queryFn: accountsApi.birthdays, staleTime: 10 * 60_000 })

  if (isError || (data && data.length === 0)) return null
  return (
    <Widget title="Cumpleaños">
      {isPending ? (
        <ListSkeleton rows={2} label="Cargando cumpleaños" />
      ) : (
        <ul className="grid grid-cols-1 gap-3">
          {data.slice(0, 5).map((person) => (
            <li key={person.id} className="flex items-center gap-3">
              <UserAvatar user={person} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-slate-900">{person.name}</p>
                <p className="text-xs text-slate-500">
                  {person.is_today ? '¡Hoy es su cumpleaños!' : monthDay.format(Date.UTC(2000, person.month - 1, person.day))}
                </p>
              </div>
              {person.is_today && <Cake className="size-5 text-accent-400" aria-hidden />}
            </li>
          ))}
        </ul>
      )}
    </Widget>
  )
}
