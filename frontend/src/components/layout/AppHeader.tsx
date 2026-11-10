import { Link } from 'react-router'

import { Logo } from '@/components/ui/Logo'
import { UserMenu } from '@/features/accounts/components/UserMenu'
import { NotificationBell } from '@/features/notifications/components/NotificationBell'

export function AppHeader() {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-surface/85 pt-[env(safe-area-inset-top)] backdrop-blur-md">
      <a href="#contenido" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:rounded-lg focus:bg-surface focus:px-3 focus:py-2">
        Saltar al contenido
      </a>
      <div className="mx-auto flex h-16 w-full max-w-shell items-center justify-between gap-4 px-4 sm:px-6">
        <Link to="/" aria-label="Ir al inicio" className="pressable rounded-lg">
          <Logo />
        </Link>
        <div className="flex items-center gap-1">
          <NotificationBell />
          <UserMenu />
        </div>
      </div>
    </header>
  )
}
