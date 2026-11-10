import { Check, Ellipsis, Mail, Trash2 } from 'lucide-react'
import { createElement } from 'react'
import { useNavigate } from 'react-router'

import { Menu } from '@/components/ui/Menu'
import { cn } from '@/lib/cn'
import { formatFullDateTime, formatRelative } from '@/lib/format'

import type { Notification } from '../types'
import { notificationColor, notificationIcon } from '../utils/appearance'

interface NotificationItemProps {
  item: Notification
  onSetRead: (isRead: boolean) => void
  onRemove: () => void
}

/**
 * Un aviso. No leído: tinte azul, título en negritas y punto azul. Tocarlo lo marca como leído y lleva
 * a donde apunta (si apunta a algo). Menú «…»: marcar leído/no leído y eliminar.
 */
export function NotificationItem({ item, onSetRead, onRemove }: NotificationItemProps) {
  const navigate = useNavigate()
  const target = item.url.startsWith('/') ? item.url : null

  function open() {
    if (!item.is_read) onSetRead(true)
    if (target) navigate(target)
  }

  return (
    <li className={cn('relative flex items-start gap-3 rounded-2xl px-3 py-3 transition-colors duration-150', item.is_read ? 'hover:bg-slate-50' : 'bg-brand-50/60 hover:bg-brand-50')}>
      <button type="button" onClick={open} className="flex min-w-0 flex-1 items-start gap-3 text-left">
        <span className={cn('grid size-11 shrink-0 place-items-center rounded-2xl', notificationColor(item.color))}>
          <NotificationIcon name={item.icon} />
        </span>
        <span className="min-w-0 flex-1">
          <span className={cn('block text-sm', item.is_read ? 'text-slate-700' : 'font-semibold text-slate-900')}>{item.title}</span>
          {item.body && <span className="mt-0.5 line-clamp-2 block text-sm text-slate-500">{item.body}</span>}
          <time dateTime={item.created_at} title={formatFullDateTime(item.created_at)} className={cn('mt-1 block text-xs', item.is_read ? 'text-slate-400' : 'font-semibold text-brand-600')}>
            {formatRelative(item.created_at)}
          </time>
        </span>
      </button>
      <div className="flex shrink-0 items-center gap-1">
        {!item.is_read && <span className="size-2.5 rounded-full bg-brand-500" aria-label="Sin leer" />}
        <Menu
          label="Opciones del aviso"
          trigger={<Ellipsis className="size-5" aria-hidden />}
          items={[
            item.is_read
              ? { label: 'Marcar como no leído', icon: Mail, onSelect: () => onSetRead(false) }
              : { label: 'Marcar como leído', icon: Check, onSelect: () => onSetRead(true) },
            { label: 'Eliminar', icon: Trash2, onSelect: onRemove, danger: true },
          ]}
        />
      </div>
    </li>
  )
}

/** Ícono traducido del nombre que manda el servidor (fuera del render del aviso: no se recrea en cada pintado). */
function NotificationIcon({ name }: { name: string }) {
  // Los íconos de Lucide ya son componentes estables; solo se elige cuál.
  return createElement(notificationIcon(name), { className: 'size-5', 'aria-hidden': true })
}
