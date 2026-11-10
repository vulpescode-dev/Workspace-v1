export const notificationsKeys = {
  all: ['notifications'] as const,
  unreadCount: () => [...notificationsKeys.all, 'unread-count'] as const,
  lists: () => [...notificationsKeys.all, 'list'] as const,
  list: (unreadOnly: boolean) => [...notificationsKeys.lists(), { unreadOnly }] as const,
}
