import { LogOut } from 'lucide-react'
import type { ReactNode } from 'react'
import { NavLink } from 'react-router'

import { menuSections, primaryNav, type NavItem } from '@/app/navigation'
import { CountBadge } from '@/components/ui/CountBadge'
import { useSectionAccess } from '@/features/accounts/hooks/useCan'
import { useLogout } from '@/features/auth/hooks/useLogout'
import { useUnreadCount } from '@/features/notifications/hooks/useUnreadCount'
import { cn } from '@/lib/cn'

import { LegalFooter } from './LegalFooter'

const itemClass = 'pressable flex h-9 items-center gap-3 rounded-xl px-3 text-sm transition-colors duration-150'

/**
 * Menú lateral de escritorio (≥ 1024 px): columna fija junto al contenido, dentro del mismo contenedor
 * que el encabezado (su borde izquierdo queda alineado con el logo). Mismas secciones que la barra
 * inferior + la hoja «Más» (`app/navigation.ts`). Cambiar de sección no se anima.
 */
export function SideNav({ className }: { className?: string }) {
  const { data: unread = 0 } = useUnreadCount()
  const logout = useLogout()
  const { canSee } = useSectionAccess()
  // Sin acceso a una sección no aparece; un grupo que se queda vacío tampoco.
  const visibleSections = menuSections
    .map((section) => ({ ...section, items: section.items.filter((item) => !item.section || canSee(item.section)) }))
    .filter((section) => section.items.length > 0)

  return (
    <aside className={className}>
      <nav
        aria-label="Menú lateral"
        className="sticky top-16 flex max-h-[calc(100dvh-4rem)] flex-col gap-5 overflow-y-auto overscroll-contain py-6 pr-2 [scrollbar-color:transparent_transparent] [scrollbar-width:thin] hover:[scrollbar-color:var(--color-slate-300)_transparent]"
      >
        <NavSection title="Principal">
          {primaryNav.map((item) => (
            <SideLink key={item.to} item={item} count={item.to === '/notifications' ? unread : 0} />
          ))}
        </NavSection>

        {visibleSections.map((section) => (
          <NavSection key={section.title} title={section.title}>
            {section.items.map((item) => (
              <SideLink key={item.to} item={item} />
            ))}
            {section.title === 'Cuenta' && (
              <li>
                <button type="button" onClick={logout} className={cn(itemClass, 'w-full font-medium text-slate-600 hover:bg-red-50 hover:text-red-600')}>
                  <LogOut className="size-5 shrink-0" aria-hidden />
                  Cerrar sesión
                </button>
              </li>
            )}
          </NavSection>
        ))}

        <LegalFooter className="px-3" />
      </nav>
    </aside>
  )
}

function NavSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h2 className="px-3 pb-1.5 font-sans text-xs font-semibold tracking-wide text-slate-400 uppercase">{title}</h2>
      <ul className="grid gap-0.5">{children}</ul>
    </section>
  )
}

function SideLink({ item, count = 0 }: { item: NavItem; count?: number }) {
  return (
    <li>
      <NavLink
        to={item.to}
        end={item.to === '/' || item.to === '/profile'}
        aria-label={count ? `${item.label}, ${count} sin leer` : undefined}
        className={({ isActive }) =>
          cn(
            itemClass,
            isActive ? 'bg-brand-50 font-semibold text-brand-700' : 'font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900',
          )
        }
      >
        {({ isActive }) => (
          <>
            <item.icon className={cn('size-5 shrink-0', isActive ? 'text-brand-600' : 'text-slate-400')} strokeWidth={isActive ? 2.25 : 1.75} aria-hidden />
            <span className="truncate">{item.label}</span>
            <CountBadge count={count} className="static ml-auto ring-0" />
          </>
        )}
      </NavLink>
    </li>
  )
}
