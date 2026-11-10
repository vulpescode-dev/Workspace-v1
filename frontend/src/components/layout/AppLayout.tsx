import { Outlet, useMatches } from 'react-router'

import { cn } from '@/lib/cn'

import { AppHeader } from './AppHeader'
import { BottomNav } from './navigation/BottomNav'
import { SideNav } from './navigation/SideNav'

/**
 * Armazón de las páginas con sesión.
 * - < 1024 px: encabezado + contenido + barra inferior. El contenido deja abajo el alto de la barra + la zona segura.
 * - ≥ 1024 px: encabezado + menú lateral fijo (15 rem) + contenido, sin barra inferior.
 * Encabezado, menú y contenido comparten un solo contenedor (`max-w-shell`): el encabezado nunca cambia
 * de ancho y el menú queda alineado con el logo; el contenido se adapta al espacio que queda.
 * Rutas con `handle: { fullWidth: true }` (perfil) van sin menú lateral y usan todo el contenedor.
 */
export function AppLayout() {
  const fullWidth = useMatches().some((match) => (match.handle as { fullWidth?: boolean } | undefined)?.fullWidth)
  return (
    <div className="min-h-dvh">
      <AppHeader />
      <div className={cn('mx-auto w-full max-w-shell px-4 sm:px-6', !fullWidth && 'lg:grid lg:grid-cols-[15rem_minmax(0,1fr)] lg:gap-8')}>
        {!fullWidth && <SideNav className="hidden lg:block" />}
        <main id="contenido" className="min-w-0 pt-6 pb-[calc(6rem+env(safe-area-inset-bottom))] sm:pt-8 lg:pb-12">
          <Outlet />
        </main>
      </div>
      <BottomNav />
    </div>
  )
}
