import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { refreshAccessToken } from '@/lib/api/client'
import { tokenStore } from '@/lib/api/token-store'
import { clearProtectedFiles } from '@/lib/media/protected-files'

import { authApi } from '../api/auth.api'
import type { AuthStatus, LoginCredentials } from '../types'
import { AuthContext } from './auth-context'

/**
 * Estado de la sesión. Al abrir la app intenta recuperar la sesión con la cookie del refresh
 * (`loading` mientras tanto); si en cualquier momento el token se pierde (refresh vencido o
 * revocado), pasa a `unauthenticated` y los guards llevan al login.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<AuthStatus>(() => (tokenStore.get() ? 'authenticated' : 'loading'))

  useEffect(() => {
    const unsubscribe = tokenStore.subscribe((token) => setStatus(token ? 'authenticated' : 'unauthenticated'))
    if (!tokenStore.get()) void refreshAccessToken()
    return () => {
      unsubscribe()
    }
  }, [])

  const login = useCallback(async (credentials: LoginCredentials) => {
    tokenStore.set(await authApi.login(credentials))
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      tokenStore.set(null)
      queryClient.clear()   // nada de los datos de esta persona queda en caché
      clearProtectedFiles()
    }
  }, [queryClient])

  const value = useMemo(() => ({ status, login, logout }), [status, login, logout])
  return <AuthContext value={value}>{children}</AuthContext>
}
