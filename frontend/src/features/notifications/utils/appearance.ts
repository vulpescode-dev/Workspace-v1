import {
  Bell, Heart, Headset, type LucideIcon, Megaphone, MessageCircle, PartyPopper, Smile, UserPlus, Wrench,
} from 'lucide-react'

/**
 * El servidor guarda el ícono con su nombre de Boxicons (frontend anterior) y el color con nombre.
 * Aquí se traducen a Lucide y a los colores de la marca. Un ícono nuevo sin traducción usa la campana.
 */
const ICONS: Record<string, LucideIcon> = {
  'bx-bell': Bell,
  'bx-heart': Heart,
  'bx-smile': Smile,
  'bx-comment': MessageCircle,
  'bx-user-plus': UserPlus,
  'bx-party': PartyPopper,
  'bx-wrench': Wrench,
  'bx-support': Headset,
  'bx-megaphone': Megaphone,
}

const COLORS: Record<string, string> = {
  primary: 'bg-brand-50 text-brand-600',
  secondary: 'bg-accent-100 text-accent-900',
  info: 'bg-sky-50 text-sky-600',
  warning: 'bg-amber-50 text-amber-600',
  danger: 'bg-red-50 text-red-600',
  success: 'bg-emerald-50 text-emerald-600',
}

export const notificationIcon = (name: string) => ICONS[name] ?? Bell
export const notificationColor = (name: string) => COLORS[name] ?? COLORS.primary

/** Agrupa por día para la lista: Hoy · Ayer · Esta semana · Anteriores (en la zona de quien la ve). */
export function dayGroup(iso: string, now = new Date()): string {
  const date = new Date(iso)
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const day = 86_400_000
  if (date.getTime() >= startOfToday) return 'Hoy'
  if (date.getTime() >= startOfToday - day) return 'Ayer'
  if (date.getTime() >= startOfToday - 6 * day) return 'Esta semana'
  return 'Anteriores'
}
