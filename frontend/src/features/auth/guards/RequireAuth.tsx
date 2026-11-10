import { Navigate, Outlet, useLocation } from 'react-router'

import { FullPageLoader } from '@/components/feedback/FullPageLoader'

import { useAuth } from '../context/useAuth'

/** Rutas privadas: sin sesión → /login?next=<ruta actual>. */
export function RequireAuth() {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <FullPageLoader />
  if (status === 'unauthenticated') {
    const next = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/login?next=${next}`} replace />
  }
  return <Outlet />
}
