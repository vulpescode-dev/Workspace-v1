import { ChevronDown, LogOut, UserRound } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'

import { cn } from '@/lib/cn'
import { useLogout } from '@/features/auth/hooks/useLogout'

import { useMe } from '../hooks/useMe'
import { UserAvatar } from './UserAvatar'

/**
 * «Mi cuenta» en el encabezado. El menú crece desde el botón (origen arriba a la derecha) con
 * opacidad + scale(.97) en 150 ms ease-out; se cierra con Escape, clic fuera o al elegir una opción.
 */
export function UserMenu() {
  const { data: me } = useMe()
  const logout = useLogout()
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onPointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false)
    }
    const onKeyDown = (event: KeyboardEvent) => event.key === 'Escape' && setOpen(false)
    document.addEventListener('pointerdown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('pointerdown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  async function handleLogout() {
    setOpen(false)
    await logout()
  }

  if (!me) return <span className="size-10 animate-pulse rounded-full bg-slate-200" aria-hidden />

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="pressable flex items-center gap-2 rounded-full py-1 pr-2 pl-1 transition-colors duration-150 hover:bg-slate-100"
      >
        <UserAvatar user={me} size="sm" />
        <span className="hidden max-w-40 truncate text-sm font-semibold text-slate-700 sm:block">{me.name}</span>
        <ChevronDown className="size-4 text-slate-400" aria-hidden />
      </button>

      <div
        role="menu"
        aria-label="Mi cuenta"
        className={cn(
          'absolute right-0 mt-2 w-64 origin-top-right rounded-2xl border border-slate-200/70 bg-surface p-1.5 shadow-lg shadow-slate-900/10',
          'transition-[opacity,transform,visibility] duration-150 ease-out',
          open ? 'visible scale-100 opacity-100' : 'invisible scale-[.97] opacity-0',
        )}
      >
        <div className="px-3 py-2.5">
          <p className="truncate text-sm font-semibold text-slate-900">{me.name}</p>
          <p className="truncate text-xs text-slate-500">{me.email}</p>
        </div>
        <div className="my-1 h-px bg-slate-100" />
        <Link
          to="/profile"
          role="menuitem"
          onClick={() => setOpen(false)}
          tabIndex={open ? 0 : -1}
          className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          <UserRound className="size-4 text-slate-400" aria-hidden />
          Ver mi perfil
        </Link>
        <button
          type="button"
          role="menuitem"
          onClick={handleLogout}
          tabIndex={open ? 0 : -1}
          className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          <LogOut className="size-4 text-slate-400" aria-hidden />
          Cerrar sesión
        </button>
      </div>
    </div>
  )
}
