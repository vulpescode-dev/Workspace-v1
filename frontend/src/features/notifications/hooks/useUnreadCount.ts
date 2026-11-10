import { useQuery } from '@tanstack/react-query'

import { useAuth } from '@/features/auth/context/useAuth'

import { notificationsApi } from '../api/notifications.api'
import { notificationsKeys } from '../api/query-keys'

/** Avisos sin leer (globito de la campana y de la barra). Sin WebSockets: se consulta cada minuto. */
export function useUnreadCount() {
  const { status } = useAuth()
  return useQuery({
    queryKey: notificationsKeys.unreadCount(),
    queryFn: notificationsApi.unreadCount,
    enabled: status === 'authenticated',
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  })
}
