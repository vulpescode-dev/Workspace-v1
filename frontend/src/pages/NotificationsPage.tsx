import { CheckCheck } from 'lucide-react'
import { useSearchParams } from 'react-router'

import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Tabs } from '@/components/ui/Tabs'
import { NotificationList } from '@/features/notifications/components/NotificationList'
import { useNotificationActions } from '@/features/notifications/hooks/useNotifications'
import { useUnreadCount } from '@/features/notifications/hooks/useUnreadCount'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'

/** /notifications — Avisos: Todos · No leídos (en la URL) y «Marcar todo como leído». */
export function NotificationsPage() {
  useDocumentTitle('Avisos')
  const [params, setParams] = useSearchParams()
  const unreadOnly = params.get('filter') === 'unread'
  const { data: unread = 0 } = useUnreadCount()
  const { readAll } = useNotificationActions()

  return (
    <div className="w-full">
      <PageHeader
        title="Avisos"
        description={unread > 0 ? `Tienes ${unread} ${unread === 1 ? 'aviso sin leer' : 'avisos sin leer'}.` : 'Estás al día.'}
        actions={
          <Button variant="outline" size="sm" onClick={() => readAll.mutate()} disabled={unread === 0} loading={readAll.isPending}>
            <CheckCheck className="size-4" aria-hidden /> Marcar todo como leído
          </Button>
        }
      />
      <Tabs
        label="Filtrar avisos"
        options={[
          { value: 'all', label: 'Todos' },
          { value: 'unread', label: unread > 0 ? `No leídos (${unread})` : 'No leídos' },
        ]}
        value={unreadOnly ? 'unread' : 'all'}
        onChange={(next) => setParams(next === 'unread' ? { filter: 'unread' } : {}, { replace: true })}
        className="mb-4"
      />
      <NotificationList unreadOnly={unreadOnly} />
    </div>
  )
}
