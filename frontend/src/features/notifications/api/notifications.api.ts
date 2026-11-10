import { api } from '@/lib/api/client'
import type { Paginated } from '@/types/api'

import type { Notification } from '../types'

export const notificationsApi = {
  unreadCount: () => api.get<{ unread: number }>('/notifications/unread-count/').then(({ data }) => data.unread),
  list: (page: number, unreadOnly: boolean) =>
    api.get<Paginated<Notification>>('/notifications/', { params: { page, unread: unreadOnly ? 1 : undefined } }).then(({ data }) => data),
  setRead: (id: number, isRead: boolean) => api.patch<Notification>(`/notifications/${id}/`, { is_read: isRead }).then(({ data }) => data),
  remove: (id: number) => api.delete(`/notifications/${id}/`),
  readAll: () => api.post<{ updated: number; unread: number }>('/notifications/read-all/').then(({ data }) => data),
}
