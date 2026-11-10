import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { ArrowLeft, CheckCircle2, FileX, Lock, RotateCcw, SendHorizontal, XCircle } from 'lucide-react'
import { useState, type FormEvent, type ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'

import { useCan } from '@/features/accounts/hooks/useCan'
import { EmptyState } from '@/components/feedback/EmptyState'
import { Skeleton } from '@/components/feedback/Skeleton'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { useMe } from '@/features/accounts/hooks/useMe'
import {
  categoryLabel, helpdeskApi, helpdeskKeys, PRIORITY_LABELS, STATUS_LABELS, type TicketCategory, type TicketChanges, type TicketDetail,
  type TicketPriority, type TicketStatus,
} from '@/features/helpdesk/api/helpdesk.api'
import { PriorityBadge, StatusBadge, UnclassifiedBadge } from '@/features/helpdesk/components/TicketBadges'
import { TicketConversation } from '@/features/helpdesk/components/TicketConversation'
import { FilePicker } from '@/features/helpdesk/components/TicketFiles'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { getErrorMessage } from '@/lib/api/errors'
import { cn } from '@/lib/cn'
import { formatFullDateTime, formatRelative } from '@/lib/format'

const selectClass = 'h-10 w-full rounded-xl border border-slate-200 bg-surface px-3 text-base text-slate-900 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none disabled:opacity-60 sm:text-sm'

/**
 * /helpdesk/:id — un ticket: conversación con su historial, caja para responder y, para los agentes del
 * departamento, el panel para atenderlo (estado, prioridad, responsable, transferir). Quien lo levantó
 * confirma la solución (cierra) o lo reabre.
 */
export function TicketPage() {
  const id = Number(useParams().ticketId)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: me } = useMe()
  const ticket = useQuery({ queryKey: helpdeskKeys.detail(id), queryFn: () => helpdeskApi.get(id), enabled: Number.isInteger(id) })
  useDocumentTitle(ticket.data ? `${ticket.data.folio} · ${ticket.data.title}` : 'Ticket')

  const update = useMutation({
    mutationFn: (changes: TicketChanges) => helpdeskApi.update(id, changes),
    onSuccess: (result, changes) => {
      void queryClient.invalidateQueries({ queryKey: helpdeskKeys.lists() })
      if ('visible' in result) {
        toast.success(result.department ? `Ticket transferido a ${result.department.name}.` : 'Ticket actualizado.')
        queryClient.removeQueries({ queryKey: helpdeskKeys.detail(id) })
        navigate('/helpdesk', { replace: true })
        return
      }
      queryClient.setQueryData(helpdeskKeys.detail(id), result)
      void queryClient.invalidateQueries({ queryKey: helpdeskKeys.agents(id) })
      if (changes.status === 'closed') toast.success('Ticket cerrado.')
      else if (changes.status === 'open' && !result.permissions.attend) toast.success('Ticket reabierto: el equipo ya está avisado.')
    },
    onError: (error) => toast.error(getErrorMessage(error, 'No se pudo guardar el cambio.')),
  })

  const back = (
    <Link to="/helpdesk" className="inline-flex w-fit items-center gap-2 rounded-lg text-sm font-semibold text-slate-500 hover:text-slate-800">
      <ArrowLeft className="size-4" aria-hidden /> Mesa de ayuda
    </Link>
  )

  if (ticket.isPending) {
    return (
      <div className="grid gap-4">
        {back}
        <Card className="grid gap-3 p-5"><Skeleton className="h-4 w-24" /><Skeleton className="h-7 w-2/3" /><Skeleton className="h-4 w-1/2" /></Card>
        <Card className="grid gap-4 p-5"><Skeleton className="h-20" /><Skeleton className="h-16 w-3/4" /></Card>
      </div>
    )
  }
  if (ticket.isError) {
    const gone = isAxiosError(ticket.error) && ticket.error.response?.status === 404
    return (
      <div className="grid gap-4">
        {back}
        <Card>
          <EmptyState icon={FileX} title={gone ? 'Este ticket no está disponible' : 'No se pudo cargar el ticket'} description={gone ? 'Puede que no exista o que no tengas acceso a él.' : undefined}
            action={gone ? undefined : <Button variant="outline" onClick={() => void ticket.refetch()}>Reintentar</Button>} />
        </Card>
      </div>
    )
  }

  const data = ticket.data
  const { permissions } = data
  const requesterView = data.requester.id === me?.id && !permissions.attend

  return (
    <div className="grid gap-4">
      {back}
      <Card className="p-5 sm:p-6">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-sm font-semibold text-slate-500">{data.folio}</span>
          <StatusBadge status={data.status} />
          <PriorityBadge priority={data.priority} />
        </div>
        <h1 className="mt-2 text-xl font-bold break-words text-slate-900 sm:text-2xl">{data.title}</h1>
        <p className="mt-1 flex flex-wrap items-center gap-x-1.5 gap-y-1 text-sm text-slate-500">
          {data.department ? <>{categoryLabel(data)} · {data.department.name}</> : <>Otro · <UnclassifiedBadge /></>}
        </p>
        {!data.department && permissions.attend && (
          <p className="mt-3 rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-800">
            No estaba en la lista de problemas. Si es de tu área, ponle categoría en «Clasificar» y pasará a ese departamento.
          </p>
        )}
      </Card>

      {requesterView && permissions.reopen && (
        <Card className="flex flex-col gap-3 border-emerald-200 bg-emerald-50/60 p-4 sm:flex-row sm:items-center">
          <p className="flex-1 text-sm text-emerald-900"><strong>El equipo marcó tu ticket como resuelto.</strong> ¿Quedó solucionado?</p>
          <div className="flex gap-2">
            <Button size="sm" loading={update.isPending && update.variables?.status === 'closed'} onClick={() => update.mutate({ status: 'closed' })}><CheckCircle2 className="size-4" aria-hidden /> Sí, cerrar</Button>
            <Button size="sm" variant="outline" loading={update.isPending && update.variables?.status === 'open'} onClick={() => update.mutate({ status: 'open' })}><RotateCcw className="size-4" aria-hidden /> No, reabrir</Button>
          </div>
        </Card>
      )}

      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="grid gap-4">
          <Card className="p-4 sm:p-5">
            <TicketConversation ticket={data} meId={me?.id} />
          </Card>
          {permissions.comment ? (
            <Composer ticket={data} />
          ) : data.status === 'closed' && (
            <p className="text-center text-sm text-slate-500">Este ticket está cerrado. Si el problema regresa, levanta uno nuevo.</p>
          )}
        </div>

        <aside className="grid gap-4 lg:sticky lg:top-24">
          {permissions.attend && <AttendPanel ticket={data} meId={me?.id} saving={update.isPending} onChange={(changes) => update.mutate(changes)} />}
          <Card className="p-4">
            <dl className="grid gap-3 text-sm">
              <Detail label="Lo levantó"><Person user={data.requester} /></Detail>
              <Detail label="Responsable">{data.assignee ? <Person user={data.assignee} /> : <span className="text-slate-500">Sin asignar</span>}</Detail>
              <Detail label="Creado"><time dateTime={data.created_at} title={formatFullDateTime(data.created_at)}>{formatRelative(data.created_at)}</time></Detail>
              {data.first_response_at && <Detail label="Primera respuesta"><time dateTime={data.first_response_at} title={formatFullDateTime(data.first_response_at)}>{formatRelative(data.first_response_at)}</time></Detail>}
              {data.closed_at && <Detail label="Cerrado"><time dateTime={data.closed_at} title={formatFullDateTime(data.closed_at)}>{formatRelative(data.closed_at)}</time></Detail>}
            </dl>
            {requesterView && permissions.close && data.status !== 'resolved' && (
              <Button variant="ghost" size="sm" className="mt-3 w-full text-slate-500" loading={update.isPending}
                onClick={() => window.confirm('¿Cerrar este ticket? Úsalo si ya no lo necesitas; después no se puede reabrir.') && update.mutate({ status: 'closed' })}>
                <XCircle className="size-4" aria-hidden /> Ya no lo necesito, cerrar
              </Button>
            )}
          </Card>
        </aside>
      </div>
    </div>
  )
}

function Detail({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid gap-1">
      <dt className="text-xs font-medium text-slate-500">{label}</dt>
      <dd className="min-w-0 text-slate-800">{children}</dd>
    </div>
  )
}

function Person({ user }: { user: { id: number; name: string; initials: string; avatar_url: string } }) {
  return (
    <Link to={`/profile/${user.id}`} className="flex min-w-0 items-center gap-2 hover:underline">
      <UserAvatar user={user} size="sm" /><span className="truncate font-medium">{user.name}</span>
    </Link>
  )
}

/** Panel del agente: cada cambio se guarda al momento y queda en el historial. */
function AttendPanel({ ticket, meId, saving, onChange }: { ticket: TicketDetail; meId?: number; saving: boolean; onChange: (changes: TicketChanges) => void }) {
  const canAssign = useCan()('helpdesk.tickets.assign')
  const agents = useQuery({ queryKey: helpdeskKeys.agents(ticket.id), queryFn: () => helpdeskApi.agents(ticket.id), staleTime: 60_000 })
  const categories = useQuery({ queryKey: helpdeskKeys.categories(), queryFn: helpdeskApi.categories, staleTime: 10 * 60_000 })
  const groups = new Map<string, TicketCategory[]>()
  for (const item of categories.data ?? []) groups.set(item.department.name, [...(groups.get(item.department.name) ?? []), item])
  const current = ticket.category
  const hasCurrent = !current || categories.data?.some((item) => item.id === current.id)

  return (
    <Card className="grid gap-3 p-4">
      <h2 className="text-sm font-bold text-slate-900">Atender</h2>
      {!ticket.assignee && meId && agents.data?.some((agent) => agent.id === meId) && (
        <Button size="sm" disabled={saving} onClick={() => onChange({ assignee: meId, ...(ticket.status === 'open' && { status: 'in_progress' as const }) })}>
          Tomar ticket
        </Button>
      )}
      <PanelField label="Estado">
        <select value={ticket.status} disabled={saving} onChange={(event) => {
          const status = event.target.value as TicketStatus
          if (status === 'closed' && !window.confirm('¿Cerrar el ticket? Ya no se podrá responder ni cambiar.')) return
          onChange({ status })
        }} className={selectClass}>
          {(Object.keys(STATUS_LABELS) as TicketStatus[]).map((value) => <option key={value} value={value}>{STATUS_LABELS[value]}</option>)}
        </select>
      </PanelField>
      <PanelField label="Prioridad">
        <select value={ticket.priority} disabled={saving} onChange={(event) => onChange({ priority: event.target.value as TicketPriority })} className={selectClass}>
          {(Object.keys(PRIORITY_LABELS) as TicketPriority[]).map((value) => <option key={value} value={value}>{PRIORITY_LABELS[value]}</option>)}
        </select>
      </PanelField>
      <PanelField label="Responsable">
        <select value={ticket.assignee?.id ?? 0} disabled={saving || agents.isPending} onChange={(event) => onChange({ assignee: Number(event.target.value) || null })} className={selectClass}>
          <option value={0}>Sin asignar</option>
          {ticket.assignee && !agents.data?.some((agent) => agent.id === ticket.assignee!.id) && <option value={ticket.assignee.id}>{ticket.assignee.name}</option>}
          {/* Sin «assign» solo se puede tomar uno mismo (o soltarlo): no se ofrece a otras personas. */}
          {agents.data?.filter((agent) => canAssign || agent.id === meId || agent.id === ticket.assignee?.id).map((agent) => <option key={agent.id} value={agent.id}>{agent.name}</option>)}
        </select>
      </PanelField>
      <PanelField label={current ? 'Categoría' : 'Clasificar'} hint={current ? 'Cambiarla a la de otro departamento lo transfiere.' : 'Elige el problema y el ticket pasará al departamento que lo atiende.'}>
        <select value={current?.id ?? 0} disabled={saving || categories.isPending} onChange={(event) => {
          const next = categories.data?.find((item) => item.id === Number(event.target.value))
          if (next && ticket.department && next.department.id !== ticket.department.id && !window.confirm(`¿Transferir el ticket a ${next.department.name}? Su equipo lo atenderá.`)) return
          onChange({ category: Number(event.target.value) })
        }} className={selectClass}>
          {!current && <option value={0} disabled>Otro: elige la categoría</option>}
          {current && !hasCurrent && <option value={current.id}>{current.name}</option>}
          {[...groups].map(([department, items]) => (
            <optgroup key={department} label={department}>{items.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</optgroup>
          ))}
        </select>
      </PanelField>
    </Card>
  )
}

function PanelField({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="grid gap-1">
      <span className="text-xs font-semibold text-slate-600">{label}</span>
      {children}
      {hint && <span className="text-[11px] text-slate-500">{hint}</span>}
    </label>
  )
}

/** Responder: texto y/o archivos. Los agentes pueden marcarlo como nota interna (no la ve quien lo levantó). */
function Composer({ ticket }: { ticket: TicketDetail }) {
  const queryClient = useQueryClient()
  const [body, setBody] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [internal, setInternal] = useState(false)
  const send = useMutation({
    mutationFn: () => {
      const form = new FormData()
      form.append('body', body.trim())
      form.append('is_internal', internal ? 'true' : 'false')
      files.forEach((file) => form.append('files', file))
      return helpdeskApi.comment(ticket.id, form)
    },
    onSuccess: (result) => {
      queryClient.setQueryData(helpdeskKeys.detail(ticket.id), result)
      void queryClient.invalidateQueries({ queryKey: helpdeskKeys.lists() })
      setBody('')
      setFiles([])
      setInternal(false)
    },
    onError: (error) => toast.error(getErrorMessage(error, 'No se pudo enviar.')),
  })

  function submit(event: FormEvent) {
    event.preventDefault()
    if ((body.trim() || files.length) && !send.isPending) send.mutate()
  }

  return (
    <Card className={cn('p-3 transition-colors duration-150 sm:p-4', internal && 'border-amber-200 bg-amber-50/50')}>
      <form onSubmit={submit} className="grid gap-2">
        <textarea
          value={body}
          onChange={(event) => setBody(event.target.value)}
          onKeyDown={(event) => { if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) submit(event) }}
          rows={3}
          maxLength={5000}
          aria-label="Respuesta"
          placeholder={internal ? 'Nota para el equipo (no la ve quien levantó el ticket)…' : ticket.permissions.attend ? `Responder a ${ticket.requester.name}…` : 'Escribe tu respuesta…'}
          className="w-full resize-y rounded-xl border border-slate-200 bg-surface px-4 py-3 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm"
        />
        <div className="flex flex-wrap items-center gap-2">
          <FilePicker files={files} onChange={setFiles} compact />
          {ticket.permissions.internal_notes && (
            <label className={cn('flex h-9 cursor-pointer items-center gap-2 rounded-xl px-2.5 text-sm font-semibold select-none', internal ? 'text-amber-800' : 'text-slate-600')}>
              <input type="checkbox" checked={internal} onChange={(event) => setInternal(event.target.checked)} className="size-4 rounded accent-amber-500" />
              <Lock className="size-3.5" aria-hidden /> Nota interna
            </label>
          )}
          <Button type="submit" size="sm" className="ml-auto" loading={send.isPending} disabled={!body.trim() && !files.length}>
            <SendHorizontal className="size-4" aria-hidden /> {internal ? 'Guardar nota' : 'Enviar'}
          </Button>
        </div>
      </form>
    </Card>
  )
}
