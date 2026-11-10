import { useQuery } from '@tanstack/react-query'

import { useAuth } from '@/features/auth/context/useAuth'

import { accountsApi } from '../api/accounts.api'
import { accountsKeys } from '../api/query-keys'

/** Mi perfil. Solo se pide con sesión iniciada. */
export function useMe() {
  const { status } = useAuth()
  return useQuery({
    queryKey: accountsKeys.me(),
    queryFn: accountsApi.me,
    enabled: status === 'authenticated',
  })
}
