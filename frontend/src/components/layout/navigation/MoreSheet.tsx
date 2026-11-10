import { LogOut } from 'lucide-react'
import { NavLink } from 'react-router'
import { Drawer } from 'vaul'

import { menuSections } from '@/app/navigation'
import { useSectionAccess } from '@/features/accounts/hooks/useCan'
import { useLogout } from '@/features/auth/hooks/useLogout'
import { cn } from '@/lib/cn'

import { LegalFooter } from './LegalFooter'

/**
 * Hoja «Más» (Vaul, de Emil Kowalski): sube desde abajo con la curva tipo iOS, se cierra arrastrando
 * (basta un movimiento rápido), tocando fuera o con Escape. Las apps van en cuadrícula de 3 (como un
 * lanzador), luego la cuenta y al final el pie legal.
 */
export function MoreSheet({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const { canSee } = useSectionAccess()
  // Sin acceso a una sección no aparece; un grupo que se queda vacío tampoco.
  const visibleSections = menuSections
    .map((section) => ({ ...section, items: section.items.filter((item) => !item.section || canSee(item.section)) }))
    .filter((section) => section.items.length > 0)
  const logout = useLogout()
  const close = () => onOpenChange(false)

  async function handleLogout() {
    close()
    await logout()
  }

  return (
    <Drawer.Root open={open} onOpenChange={onOpenChange}>
      <Drawer.Portal>
        <Drawer.Overlay className="fixed inset-0 z-50 bg-slate-950/40" />
        <Drawer.Content
          aria-describedby={undefined}
          className="fixed inset-x-0 bottom-0 z-50 mx-auto flex max-h-[88dvh] max-w-md flex-col rounded-t-3xl bg-surface pb-[env(safe-area-inset-bottom)] outline-none"
        >
          <div aria-hidden className="mx-auto mt-3 mb-1 h-1.5 w-10 shrink-0 rounded-full bg-slate-300" />
          <Drawer.Title className="px-5 pt-2 pb-1 font-display text-lg font-bold text-slate-900">Menú</Drawer.Title>

          <div className="overflow-y-auto overscroll-contain px-3 pb-4">
            {visibleSections.map((section) => (
              <section key={section.title} className="mt-3">
                <h2 className="px-2 pb-2 font-sans text-xs font-semibold tracking-wide text-slate-400 uppercase">{section.title}</h2>
                <ul className="grid grid-cols-3 gap-1">
                  {section.items.map((item) => (
                    <li key={item.to}>
                      <NavLink
                        to={item.to}
                        end={item.to === '/profile'}
                        onClick={close}
                        className={({ isActive }) =>
                          cn(
                            'pressable flex flex-col items-center gap-2 rounded-2xl px-1 py-3 text-center transition-colors duration-150 hover:bg-slate-50',
                            isActive && 'bg-brand-50',
                          )
                        }
                      >
                        {({ isActive }) => (
                          <>
                            <span className={cn('grid size-12 place-items-center rounded-2xl', isActive ? 'bg-brand-500 text-white' : 'bg-brand-50 text-brand-600')}>
                              <item.icon className="size-[22px]" aria-hidden />
                            </span>
                            <span className="text-xs leading-tight font-medium text-slate-700">{item.label}</span>
                          </>
                        )}
                      </NavLink>
                    </li>
                  ))}
                </ul>
              </section>
            ))}

            <button
              type="button"
              onClick={handleLogout}
              className="pressable mt-4 flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left text-sm font-semibold text-red-600 transition-colors duration-150 hover:bg-red-50"
            >
              <span className="grid size-10 place-items-center rounded-xl bg-red-50">
                <LogOut className="size-5" aria-hidden />
              </span>
              Cerrar sesión
            </button>

            <LegalFooter onNavigate={close} className="mt-4 justify-center px-2" />
          </div>
        </Drawer.Content>
      </Drawer.Portal>
    </Drawer.Root>
  )
}
