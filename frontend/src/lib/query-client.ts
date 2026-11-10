import { QueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'

/** Caché de datos del servidor (TanStack Query). Los errores 4xx no se reintentan: no van a cambiar. */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        const status = isAxiosError(error) ? error.response?.status : undefined
        if (status && status < 500) return false
        return failureCount < 2
      },
    },
  },
})
