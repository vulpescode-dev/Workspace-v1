import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { Headset, Plus, Search } from 'lucide-react'
import { useState } from 'react'
import { Link, Navigate, useSearchParams } from 'react-router'

import { EmptyState } from '@/components/feedback/EmptyState'
import { ListSkeleton } from '@/components/feedback/ListSkeleton'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Tabs } from '@/components/ui/Tabs'
import { useCan } from '@/features/accounts/hooks/useCan'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { categoryLabel, helpdeskApi, helpdeskKeys, type Ticket, type TicketScope } from '@/features/helpdesk/api/helpdesk.api'
import { NewTicketSheet } from '@/features/helpdesk/components/NewTicketSheet'
import { PriorityBadge, StatusBadge, UnclassifiedBadge } from '@/features/helpdesk/components/TicketBadges'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { cn } from '@/lib/cn'
import { formatFullDateTime, formatRelative } from '@/lib/format'

const STATUS_FILTERS = [
  { value: 'active', label: 'Activos', statuses: 'open,in_progress,waiting' },
  { value: 'resolved', label: 'Resueltos', statuses: 'resolved' },
  { value: 'closed', label: 'Cerrados', statuses: 'closed' },
  { value: 'all', label: 'Todos', statuses: '' },
] as const

/**
 * /helpdesk — tickets. Quien atiende un departamento ve «Por atender» (su cola), «Asignados a mí» y
 * «Mis tickets»; los demás, solo los suyos. Estado, búsqueda (título o folio) y pestaña van en la URL.
 */
export function HelpdeskPage() {
  useDocumentTitle('Mesa de ayuda')
  const canCreate = useCan()('helpdesk.tickets.create')
  const [params, setParams] = useSearchParams()
  const [text, setText] = useState(params.get('q') ?? '')
  const q = useDebouncedValue(text.trim(), 300)
  const [creating, setCreating] = useState(params.get('new') === '1')
  const me = useQuery({ queryKey: helpdeskKeys.me(), queryFn: helpdeskApi.me, staleTime: 5 * 60_000 })
  const agent = Boolean(me.data && (me.data.all_departments || me.data.attends.length > 0))
  const scope = (params.get('scope') as TicketScope | null) ?? (agent ? 'queue' : 'mine')
  const statusFilter = STATUS_FILTERS.find((item) => item.value === params.get('status')) ?? STATUS_FILTERS[0]
  const unassigned = scope === 'queue' && params.get('unassigned') === '1'
  const unclassified = scope === 'queue' && params.get('unclassified') === '1'
  // En «Mis tickets», uno resuelto espera que confirme la solución: sigue contando como activo.
  const statuses = statusFilter.value === 'active' && scope === 'mine' ? `${statusFilter.statuses},resolved` : statusFilter.statuses
  const filters = { scope, status: statuses, unassigned, unclassified, q }

  const list = useInfiniteQuery({
    queryKey: helpdeskKeys.list(filters),
    queryFn: ({ pageParam }) => helpdeskApi.list(filters, pageParam),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page < last.total_pages ? last.page + 1 : undefined),
    placeholderData: (previous) => previous,
    enabled: me.isSuccess,
  })

  // Avisos viejos apuntaban a /helpdesk/?ticket=42.
  const legacy = params.get('ticket')
  if (legacy && /^\d+$/.test(legacy)) return <Navigate to={`/helpdesk/${legacy}`} replace />

  function update(next: Record<string, string>) {
    const merged = new URLSearchParams(params)
    Object.entries(next).forEach(([key, value]) => (value ? merged.set(key, value) : merged.delete(key)))
    setParams(merged, { replace: true })
  }

  const items = list.data?.pages.flatMap((page) => page.results) ?? []
  const total = list.data?.pages[0]?.count ?? 0
  const scopes = [
    { value: 'queue', label: me.data?.attends.length === 1 ? `Por atender · ${me.data.attends[0].name}` : 'Por atender' },
    { value: 'assigned', label: 'Asignados a mí' },
    { value: 'mine', label: 'Mis tickets' },
  ]

  return (
    <>
      <PageHeader
        title="Mesa de ayuda"
        description={agent ? 'Atiende las solicitudes de tu área y da seguimiento a las tuyas.' : '¿Algo no funciona o necesitas algo? Levanta un ticket y te avisamos de cada avance.'}
        actions={canCreate && <Button onClick={() => setCreating(true)}><Plus className="size-4" aria-hidden /> Nuevo ticket</Button>}
      />
      {agent && <Tabs label="Qué tickets ver" options={scopes} value={scope} onChange={(value) => update({ scope: value, unassigned: '', unclassified: '' })} className="mb-4" />}

      <Card className="mb-4 grid gap-3 p-3">
        <label className="relative">
          <span className="sr-only">Buscar tickets</span>
          <Search className="pointer-events-none absolute top-1/2 left-3.5 size-5 -translate-y-1/2 text-slate-400" aria-hidden />
          <input
            type="search"
            value={text}
            onChange={(event) => { setText(event.target.value); update({ q: event.target.value.trim() }) }}
            placeholder="Buscar por título o folio (HD-00042)"
            className="h-11 w-full rounded-xl border border-slate-200 pr-3 pl-11 text-base placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm"
          />
        </label>
        <div className="flex flex-wrap items-center gap-2">
          {STATUS_FILTERS.map((item) => {
            const active = statusFilter.value === item.value
            return (
              <button key={item.value} type="button" aria-pressed={active} onClick={() => update({ status: item.value === 'active' ? '' : item.value })}
                className={cn('pressable h-8 rounded-full px-3.5 text-sm font-semibold transition-colors duration-150', active ? 'bg-brand-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200')}>
                {item.label}
              </button>
            )
          })}
          {scope === 'queue' && (
            <div className="ml-auto flex flex-wrap items-center gap-x-4 gap-y-1 px-1">
              <label className="flex cursor-pointer items-center gap-2 text-sm font-medium text-slate-600 select-none">
                <input type="checkbox" checked={unclassified} onChange={(event) => update({ unclassified: event.target.checked ? '1' : '' })} className="size-4 rounded accent-brand-500" />
                Sin clasificar
              </label>
              <label className="flex cursor-pointer items-center gap-2 text-sm font-medium text-slate-600 select-none">
                <input type="checkbox" checked={unassigned} onChange={(event) => update({ unassigned: event.target.checked ? '1' : '' })} className="size-4 rounded accent-brand-500" />
                Sin responsable
              </label>
            </div>
          )}
        </div>
      </Card>

      {me.isPending || list.isPending ? (
        <Card className="p-4"><ListSkeleton rows={6} label="Cargando tickets" /></Card>
      ) : list.isError || me.isError ? (
        <Card><EmptyState icon={Headset} title="No se pudieron cargar los tickets" action={<Button variant="outline" onClick={() => void list.refetch()}>Reintentar</Button>} /></Card>
      ) : items.length === 0 ? (
        <Card>
          <EmptyState
            icon={Headset}
            title={q ? 'Ningún ticket coincide' : scope === 'mine' ? (statusFilter.value === 'active' ? 'No tienes tickets abiertos' : 'No hay tickets aquí') : '¡Todo al día!'}
            description={q ? 'Prueba con otras palabras o con el folio completo.' : scope === 'mine' ? (canCreate ? 'Cuando necesites ayuda, levanta un ticket con «Nuevo ticket».' : 'No tienes tickets.') : 'No hay tickets pendientes con este filtro.'}
          />
        </Card>
      ) : (
        <>
          <p className="mb-2 px-1 text-xs font-medium text-slate-500">{total} {total === 1 ? 'ticket' : 'tickets'}</p>
          <Card className={cn('overflow-hidden transition-opacity duration-150', list.isPlaceholderData && 'opacity-60')}>
            <ul className="divide-y divide-slate-100">{items.map((ticket) => <TicketRow key={ticket.id} ticket={ticket} showRequester={scope !== 'mine'} />)}</ul>
          </Card>
        </>
      )}
      {list.hasNextPage && (
        <Button variant="outline" className="mx-auto mt-4 flex" loading={list.isFetchingNextPage} onClick={() => void list.fetchNextPage()}>Ver más tickets</Button>
      )}

      {creating && <NewTicketSheet onClose={() => { setCreating(false); if (params.get('new')) update({ new: '' }) }} />}
    </>
  )
}

function TicketRow({ ticket, showRequester }: { ticket: Ticket; showRequester: boolean }) {
  const person = showRequester ? ticket.requester : ticket.assignee
  return (
    <li>
      <Link to={`/helpdesk/${ticket.id}`} className="flex items-start gap-3 px-4 py-3.5 transition-colors duration-150 hover:bg-slate-50">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="font-mono text-xs font-semibold text-slate-500">{ticket.folio}</span>
            <StatusBadge status={ticket.status} />
            {(ticket.priority === 'high' || ticket.priority === 'urgent') && <PriorityBadge priority={ticket.priority} />}
          </div>
          <p className="mt-1 truncate text-sm font-semibold text-slate-900">{ticket.title}</p>
          <p className="mt-0.5 flex min-w-0 items-center gap-1.5 text-xs text-slate-500">
            {ticket.department
              ? <span className="truncate">{categoryLabel(ticket)} · {ticket.department.name}</span>
              : <>Otro · <UnclassifiedBadge /></>}
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1.5 text-xs text-slate-500">
          <time dateTime={ticket.updated_at} title={formatFullDateTime(ticket.updated_at)}>{formatRelative(ticket.updated_at)}</time>
          {person ? (
            <span className="flex items-center gap-1.5" title={showRequester ? `Lo levantó ${person.name}` : `Lo atiende ${person.name}`}>
              <span className="hidden max-w-32 truncate sm:inline">{person.name}</span>
              <UserAvatar user={person} size="sm" />
            </span>
          ) : (
            !showRequester && <span className="rounded-full bg-slate-100 px-2 py-0.5 font-medium">Sin asignar</span>
          )}
        </div>
      </Link>
    </li>
  )
}
