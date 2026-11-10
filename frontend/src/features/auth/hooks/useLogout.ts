import { useCallback } from 'react'
import { toast } from 'sonner'

import { useAuth } from '../context/useAuth'

/** Cerrar sesión desde cualquier menú: revoca la sesión, limpia la caché y avisa con un toast. */
export function useLogout() {
  const { logout } = useAuth()
  return useCallback(async () => {
    await logout()
    toast('Cerraste sesión.')
  }, [logout])
}
