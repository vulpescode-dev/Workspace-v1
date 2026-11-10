import { BellOff, CheckCheck } from 'lucide-react'

import { EmptyState } from '@/components/feedback/EmptyState'
import { ListSkeleton } from '@/components/feedback/ListSkeleton'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

import { useNotificationActions, useNotifications } from '../hooks/useNotifications'
import type { Notification } from '../types'
import { dayGroup } from '../utils/appearance'
import { NotificationItem } from './NotificationItem'

/** Lista de avisos agrupada por día (Hoy · Ayer · Esta semana · Anteriores), 25 por página con «Ver más». */
export function NotificationList({ unreadOnly }: { unreadOnly: boolean }) {
  const list = useNotifications(unreadOnly)
  const { setRead, remove } = useNotificationActions()
  const items = list.data?.pages.flatMap((page) => page.results) ?? []

  if (list.isPending) {
    return (
      <Card className="p-4">
        <ListSkeleton rows={6} label="Cargando avisos" />
      </Card>
    )
  }
  if (list.isError) {
    return (
      <Card>
        <EmptyState icon={BellOff} title="No se pudieron cargar tus avisos" action={<Button variant="outline" onClick={() => void list.refetch()}>Reintentar</Button>} />
      </Card>
    )
  }
  if (items.length === 0) {
    return (
      <Card>
        {unreadOnly ? (
          <EmptyState icon={CheckCheck} title="Estás al día" description="No tienes avisos sin leer." />
        ) : (
          <EmptyState icon={BellOff} title="No tienes avisos" description="Aquí aparecerá lo que pase con tus publicaciones, tickets y más." />
        )}
      </Card>
    )
  }

  const groups = items.reduce<{ label: string; items: Notification[] }[]>((acc, item) => {
    const label = dayGroup(item.created_at)
    const last = acc.at(-1)
    if (last?.label === label) last.items.push(item)
    else acc.push({ label, items: [item] })
    return acc
  }, [])

  return (
    <Card className="p-2 sm:p-3">
      {groups.map((group) => (
        <section key={group.label} aria-label={group.label} className="mb-2 last:mb-0">
          <h2 className="px-3 pt-2 pb-1 font-sans text-xs font-semibold tracking-wide text-slate-400 uppercase">{group.label}</h2>
          <ul className="grid grid-cols-1 gap-1">
            {group.items.map((item) => (
              <NotificationItem
                key={item.id}
                item={item}
                onSetRead={(isRead) => setRead.mutate({ item, isRead })}
                onRemove={() => remove.mutate(item)}
              />
            ))}
          </ul>
        </section>
      ))}
      {list.hasNextPage && (
        <Button variant="ghost" size="sm" className="mt-1 w-full" loading={list.isFetchingNextPage} onClick={() => void list.fetchNextPage()}>
          Ver avisos anteriores
        </Button>
      )}
    </Card>
  )
}
