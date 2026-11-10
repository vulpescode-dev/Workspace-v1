import { cn } from '@/lib/cn'

import { PRIORITY_LABELS, STATUS_LABELS, type TicketPriority, type TicketStatus } from '../api/helpdesk.api'

const STATUS_TONES: Record<TicketStatus, string> = {
  open: 'bg-brand-50 text-brand-700',
  in_progress: 'bg-violet-50 text-violet-700',
  waiting: 'bg-amber-50 text-amber-700',
  resolved: 'bg-emerald-50 text-emerald-700',
  closed: 'bg-slate-100 text-slate-600',
}
const STATUS_DOTS: Record<TicketStatus, string> = {
  open: 'bg-brand-500', in_progress: 'bg-violet-500', waiting: 'bg-amber-500', resolved: 'bg-emerald-500', closed: 'bg-slate-400',
}

/** Estado del ticket: pastilla con punto de color (se distingue sin leer). */
export function StatusBadge({ status, className }: { status: TicketStatus; className?: string }) {
  return (
    <span className={cn('inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold', STATUS_TONES[status], className)}>
      <span className={cn('size-1.5 rounded-full', STATUS_DOTS[status])} aria-hidden />
      {STATUS_LABELS[status]}
    </span>
  )
}

/** Prioridad. Baja y Normal son discretas; Alta y Urgente llaman la atención. */
export function PriorityBadge({ priority, className }: { priority: TicketPriority; className?: string }) {
  const tone = priority === 'urgent' ? 'bg-red-50 text-red-700 ring-1 ring-red-200' : priority === 'high' ? 'bg-orange-50 text-orange-700' : 'bg-slate-100 text-slate-600'
  return <span className={cn('inline-flex shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold', tone, className)}>{PRIORITY_LABELS[priority]}</span>
}

/** «Otro» que nadie ha clasificado: lo ven todos los agentes hasta que alguien le pone categoría. */
export function UnclassifiedBadge({ className }: { className?: string }) {
  return (
    <span className={cn('inline-flex shrink-0 items-center gap-1.5 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-700', className)}>
      <span className="size-1.5 rounded-full bg-amber-500" aria-hidden />
      Sin clasificar
    </span>
  )
}
