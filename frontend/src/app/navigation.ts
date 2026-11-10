import {
  Bell, BookOpen, CalendarDays, CircleHelp, ClipboardList, FileText, Headset, House, type LucideIcon, Newspaper,
  Search, Store, UserRound, Users,
} from 'lucide-react'

import type { Section } from '@/features/accounts/access'

/**
 * Mapa de navegación: una sola fuente para la barra inferior, la hoja «Más», el menú lateral (cuando exista)
 * y las rutas «Próximamente» del router. Al terminar una sección: `ready: true` y su página en `router.tsx`.
 */
export interface NavItem {
  label: string
  to: string
  icon: LucideIcon
  /** false = la ruta muestra «Próximamente». */
  ready: boolean
  /** Sección con permisos: sin acceso no aparece en el menú (ver `features/accounts/access.ts`). */
  section?: Section
}

/** Barra inferior del teléfono (más el botón «Más»). Máximo 4 destinos: caben con etiqueta desde 320 px. */
export const primaryNav: NavItem[] = [
  { label: 'Inicio', to: '/', icon: House, ready: true },
  { label: 'Avisos', to: '/notifications', icon: Bell, ready: true },
  { label: 'Buscar', to: '/search', icon: Search, ready: true },
]

/** Hoja «Más»: el resto de la intranet, por secciones. */
export const menuSections: { title: string; items: NavItem[] }[] = [
  {
    title: 'Aplicaciones',
    items: [
      { label: 'Calendario', to: '/calendar', icon: CalendarDays, ready: true, section: 'people' },
      { label: 'Noticias', to: '/blog', icon: Newspaper, ready: true, section: 'blog' },
      { label: 'Documentos', to: '/documents', icon: FileText, ready: true, section: 'documents' },
      { label: 'Formularios', to: '/forms', icon: ClipboardList, ready: true, section: 'forms' },
      { label: 'Marketplace', to: '/marketplace', icon: Store, ready: true, section: 'marketplace' },
      { label: 'Mesa de ayuda', to: '/helpdesk', icon: Headset, ready: true, section: 'helpdesk' },
      { label: 'Personas', to: '/people', icon: Users, ready: true, section: 'people' },
    ],
  },
  {
    title: 'Cuenta',
    items: [
      { label: 'Mi perfil', to: '/profile', icon: UserRound, ready: true },
      { label: 'Ayuda', to: '/help', icon: CircleHelp, ready: false },
    ],
  },
]

/** Pie del menú (páginas legales). */
export const legalNav: NavItem[] = [
  { label: 'Términos', to: '/terms', icon: BookOpen, ready: false },
  { label: 'Privacidad', to: '/privacy', icon: BookOpen, ready: false },
]

/** Todas las secciones que aún no tienen pantalla (el router les pone «Próximamente»). */
export const pendingNav = [...primaryNav, ...menuSections.flatMap((section) => section.items), ...legalNav].filter(
  (item) => !item.ready,
)

/** ¿La ruta actual es de la hoja «Más»? (para marcar «Más» como activo en la barra). */
export function isInMoreMenu(pathname: string) {
  // «Mi perfil» solo cuenta en /profile exacto: el perfil de otra persona no es «Más».
  return [...menuSections.flatMap((section) => section.items), ...legalNav].some(
    (item) => pathname === item.to || (item.to !== '/profile' && pathname.startsWith(`${item.to}/`)),
  )
}
