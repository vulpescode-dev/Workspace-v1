import { ArrowRightLeft, CircleDot, Flag, Lock, UserCheck } from 'lucide-react'
import { Link } from 'react-router'

import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import type { UserSummary } from '@/features/accounts/types'
import { cn } from '@/lib/cn'
import { formatFullDateTime, formatRelative } from '@/lib/format'

import type { TicketAttachment, TicketDetail, TicketEvent } from '../api/helpdesk.api'
import { AttachmentList } from './TicketFiles'

type Entry =
  | { type: 'message'; key: string; at: string; author: UserSummary; body: string; internal: boolean; files: TicketAttachment[]; mine: boolean }
  | { type: 'event'; key: string; at: string; event: TicketEvent }

/** Qué pasó, en una frase: «Elena tomó el ticket», «cambió el estado a Resuelto»… */
function describe(event: TicketEvent) {
  switch (event.kind) {
    case 'status': return <>cambió el estado a <strong className="font-semibold text-slate-700">{event.new_label}</strong></>
    case 'priority': return <>cambió la prioridad a <strong className="font-semibold text-slate-700">{event.new_label}</strong></>
    case 'category': return <>{event.old_value === 'Otro' ? 'lo clasificó como' : 'lo transfirió a'} <strong className="font-semibold text-slate-700">{event.new_label}</strong></>
    case 'assignee':
      if (!event.new_value) return <>quitó a {event.old_value} como responsable</>
      if (event.new_value === event.actor.name) return <>tomó el ticket</>
      return <>asignó el ticket a <strong className="font-semibold text-slate-700">{event.new_value}</strong></>
    default: return null
  }
}
const EVENT_ICONS = { status: CircleDot, priority: Flag, category: ArrowRightLeft, assignee: UserCheck, created: CircleDot }

/**
 * La conversación del ticket en orden: la descripción inicial, las respuestas (las notas internas en ámbar,
 * solo las ven los agentes) y, entre ellas, el historial en renglones discretos.
 */
export function TicketConversation({ ticket, meId }: { ticket: TicketDetail; meId?: number }) {
  const entries: Entry[] = [
    { type: 'message' as const, key: 'description', at: ticket.created_at, author: ticket.requester, body: ticket.description, internal: false, files: ticket.attachments, mine: ticket.requester.id === meId },
    ...ticket.comments.map((comment): Entry => ({
      type: 'message', key: `c${comment.id}`, at: comment.created_at, author: comment.author, body: comment.body, internal: comment.is_internal, files: comment.attachments, mine: comment.author.id === meId,
    })),
    ...ticket.events.filter((event) => event.kind !== 'created').map((event): Entry => ({ type: 'event', key: `e${event.id}`, at: event.created_at, event })),
  ].sort((a, b) => a.at.localeCompare(b.at))

  return (
    <ol className="grid gap-4">
      {entries.map((entry) => {
        if (entry.type === 'event') {
          const Icon = EVENT_ICONS[entry.event.kind]
          return (
            <li key={entry.key} className="flex items-center gap-2 pl-3 text-xs text-slate-500">
              <span className="grid size-6 shrink-0 place-items-center rounded-full bg-slate-100 text-slate-500"><Icon className="size-3.5" aria-hidden /></span>
              <span className="min-w-0"><span className="font-medium text-slate-700">{entry.event.actor.name}</span> {describe(entry.event)}</span>
              <time dateTime={entry.at} title={formatFullDateTime(entry.at)} className="shrink-0">· {formatRelative(entry.at)}</time>
            </li>
          )
        }
        return (
          <li key={entry.key} className="flex gap-3">
            <Link to={`/profile/${entry.author.id}`} className="shrink-0"><UserAvatar user={entry.author} /></Link>
            <div className={cn('min-w-0 flex-1 rounded-2xl border px-4 py-3', entry.internal ? 'border-amber-200 bg-amber-50/70' : entry.mine ? 'border-brand-100 bg-brand-50/40' : 'border-slate-200 bg-surface')}>
              <p className="flex flex-wrap items-center gap-x-2 text-xs text-slate-500">
                <span className="text-sm font-semibold text-slate-900">{entry.author.name}</span>
                {entry.internal && <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 font-semibold text-amber-800"><Lock className="size-3" aria-hidden /> Nota interna</span>}
                <time dateTime={entry.at} title={formatFullDateTime(entry.at)}>{formatRelative(entry.at)}</time>
              </p>
              {entry.body && <p className="mt-1 text-sm break-words whitespace-pre-line text-slate-800">{entry.body}</p>}
              <AttachmentList files={entry.files} />
            </div>
          </li>
        )
      })}
    </ol>
  )
}
