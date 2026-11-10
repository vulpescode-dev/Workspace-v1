import { LayoutGrid, type LucideIcon } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { NavLink, useLocation } from 'react-router'

import { isInMoreMenu, primaryNav } from '@/app/navigation'
import { CountBadge } from '@/components/ui/CountBadge'
import { useUnreadCount } from '@/features/notifications/hooks/useUnreadCount'
import { cn } from '@/lib/cn'

import { MoreSheet } from './MoreSheet'

/**
 * Barra inferior (solo teléfono y tablet, < 1024 px): Inicio · Avisos · Buscar · Más.
 * Abajo deja la zona segura del teléfono (barra de inicio del iPhone) o, si no hay, al menos 0.5 rem:
 * así las etiquetas nunca quedan pegadas al borde.
 * El destino activo lleva una píldora de color detrás del ícono. Cambiar de pestaña NO se anima
 * (se usa decenas de veces al día); solo hay respuesta al presionar (scale .97).
 */
export function BottomNav() {
  const { pathname } = useLocation()
  const { data: unread = 0 } = useUnreadCount()
  const [moreOpen, setMoreOpen] = useState(false)

  return (
    <nav
      aria-label="Navegación principal"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200/70 bg-surface/90 pb-[max(env(safe-area-inset-bottom),0.5rem)] backdrop-blur-md lg:hidden"
    >
      <ul className="mx-auto grid h-16 max-w-md grid-cols-4 px-2">
        {primaryNav.map((item) => (
          <li key={item.to} className="contents">
            <NavLink to={item.to} end={item.to === '/'} className="pressable grid place-items-center outline-offset-[-4px]">
              {({ isActive }) => (
                <TabContent
                  icon={item.icon}
                  label={item.label}
                  active={isActive}
                  badge={item.to === '/notifications' ? <CountBadge count={unread} className="-top-1 right-2" /> : null}
                />
              )}
            </NavLink>
          </li>
        ))}
        <li className="contents">
          <button
            type="button"
            onClick={() => setMoreOpen(true)}
            aria-haspopup="dialog"
            aria-expanded={moreOpen}
            className="pressable grid place-items-center outline-offset-[-4px]"
          >
            <TabContent icon={LayoutGrid} label="Más" active={moreOpen || isInMoreMenu(pathname)} />
          </button>
        </li>
      </ul>
      <MoreSheet open={moreOpen} onOpenChange={setMoreOpen} />
    </nav>
  )
}

function TabContent({ icon: Icon, label, active, badge }: { icon: LucideIcon; label: string; active: boolean; badge?: ReactNode }) {
  return (
    <span className="flex flex-col items-center gap-1">
      <span className={cn('relative grid h-8 w-14 place-items-center rounded-full', active ? 'bg-brand-100 text-brand-700' : 'text-slate-500')}>
        <Icon className="size-[22px]" strokeWidth={active ? 2.25 : 1.75} aria-hidden />
        {badge}
      </span>
      <span className={cn('text-[11px] leading-none', active ? 'font-semibold text-brand-700' : 'font-medium text-slate-500')}>{label}</span>
      {active && <span className="sr-only">(actual)</span>}
    </span>
  )
}
