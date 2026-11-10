import { Navigate, Outlet, useSearchParams } from 'react-router'

import { FullPageLoader } from '@/components/feedback/FullPageLoader'

import { useAuth } from '../context/useAuth'
import { safeNext } from '../utils/safe-next'

/** Rutas para quien no ha entrado (login): con sesión → a donde iba o al Inicio. */
export function GuestOnly() {
  const { status } = useAuth()
  const [params] = useSearchParams()

  if (status === 'loading') return <FullPageLoader />
  if (status === 'authenticated') return <Navigate to={safeNext(params.get('next'))} replace />
  return <Outlet />
}
