/** Color con nombre que manda el servidor (`Notification.Color`). */
export type NotificationColor = 'primary' | 'secondary' | 'info' | 'warning' | 'danger' | 'success'

/** `GET /api/notifications/` */
export interface Notification {
  id: number
  title: string
  body: string
  /** Nombre de ícono del diseño anterior (Boxicons, p. ej. «bx-wrench»); se traduce en `utils/appearance.ts`. */
  icon: string
  color: NotificationColor | string
  /** Ruta interna a la que lleva (p. ej. «/posts/12/»); vacía si no lleva a ningún lado. */
  url: string
  created_at: string
  is_read: boolean
  read_at: string | null
}
