import { useInfiniteQuery, useMutation, useQueryClient, type InfiniteData } from '@tanstack/react-query'
import { toast } from 'sonner'

import { getErrorMessage } from '@/lib/api/errors'
import type { Paginated } from '@/types/api'

import { notificationsApi } from '../api/notifications.api'
import { notificationsKeys } from '../api/query-keys'
import type { Notification } from '../types'

type ListData = InfiniteData<Paginated<Notification>>

/** Mis avisos (25 por página). `unreadOnly`: solo los no leídos. */
export function useNotifications(unreadOnly: boolean) {
  return useInfiniteQuery({
    queryKey: notificationsKeys.list(unreadOnly),
    queryFn: ({ pageParam }) => notificationsApi.list(pageParam, unreadOnly),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page < last.total_pages ? last.page + 1 : undefined),
  })
}

/**
 * Marcar leído / no leído, eliminar y «marcar todo». Todo cambia al instante en las listas y en el
 * contador de la campana; si el servidor falla, se regresa a como estaba y se avisa.
 */
export function useNotificationActions() {
  const queryClient = useQueryClient()
  const unreadKey = notificationsKeys.unreadCount()

  const snapshot = () => ({
    lists: queryClient.getQueriesData<ListData>({ queryKey: notificationsKeys.lists() }),
    unread: queryClient.getQueryData<number>(unreadKey),
  })
  const restore = (saved: ReturnType<typeof snapshot>) => {
    saved.lists.forEach(([key, data]) => queryClient.setQueryData(key, data))
    queryClient.setQueryData(unreadKey, saved.unread)
  }
  const editLists = (edit: (items: Notification[]) => Notification[]) =>
    queryClient.setQueriesData<ListData>({ queryKey: notificationsKeys.lists() }, (data) =>
      data && { ...data, pages: data.pages.map((page) => ({ ...page, results: edit(page.results) })) },
    )
  const bumpUnread = (delta: number) => queryClient.setQueryData<number>(unreadKey, (count) => Math.max(0, (count ?? 0) + delta))
  const settle = () => {
    void queryClient.invalidateQueries({ queryKey: unreadKey })
    void queryClient.invalidateQueries({ queryKey: notificationsKeys.lists(), refetchType: 'none' })
  }

  const setRead = useMutation({
    mutationFn: ({ item, isRead }: { item: Notification; isRead: boolean }) => notificationsApi.setRead(item.id, isRead),
    onMutate: ({ item, isRead }) => {
      const saved = snapshot()
      if (item.is_read !== isRead) {
        editLists((items) => items.map((n) => (n.id === item.id ? { ...n, is_read: isRead } : n)))
        bumpUnread(isRead ? -1 : 1)
      }
      return saved
    },
    onError: (error, _, saved) => {
      if (saved) restore(saved)
      toast.error(getErrorMessage(error, 'No se pudo actualizar el aviso.'))
    },
    onSettled: settle,
  })

  const remove = useMutation({
    mutationFn: (item: Notification) => notificationsApi.remove(item.id),
    onMutate: (item) => {
      const saved = snapshot()
      editLists((items) => items.filter((n) => n.id !== item.id))
      if (!item.is_read) bumpUnread(-1)
      return saved
    },
    onError: (error, _, saved) => {
      if (saved) restore(saved)
      toast.error(getErrorMessage(error, 'No se pudo eliminar el aviso.'))
    },
    onSettled: settle,
  })

  const readAll = useMutation({
    mutationFn: notificationsApi.readAll,
    onMutate: () => {
      const saved = snapshot()
      editLists((items) => items.map((n) => ({ ...n, is_read: true })))
      queryClient.setQueryData(unreadKey, 0)
      return saved
    },
    onError: (error, _, saved) => {
      if (saved) restore(saved)
      toast.error(getErrorMessage(error, 'No se pudieron marcar como leídos.'))
    },
    onSuccess: () => toast('Todos tus avisos están leídos.'),
    onSettled: () => {
      settle()
      // La lista «No leídos» queda vacía: se vuelve a pedir.
      void queryClient.invalidateQueries({ queryKey: notificationsKeys.list(true) })
    },
  })

  return { setRead, remove, readAll }
}
