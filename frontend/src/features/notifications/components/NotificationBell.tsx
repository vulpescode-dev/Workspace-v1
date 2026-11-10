import { Bell } from 'lucide-react'
import { Link } from 'react-router'

import { CountBadge } from '@/components/ui/CountBadge'

import { useUnreadCount } from '../hooks/useUnreadCount'

/** Campana del encabezado → Avisos, con el número de avisos sin leer. */
export function NotificationBell() {
  const { data: unread = 0 } = useUnreadCount()
  return (
    <Link
      to="/notifications"
      aria-label={unread ? `Avisos, ${unread} sin leer` : 'Avisos'}
      className="pressable relative grid size-10 place-items-center rounded-full text-slate-600 transition-colors duration-150 hover:bg-slate-100"
    >
      <Bell className="size-5" aria-hidden />
      <CountBadge count={unread} className="top-1 right-0.5" />
    </Link>
  )
}
