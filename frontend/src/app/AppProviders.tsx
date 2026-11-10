import { QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { Toaster } from 'sonner'

import { AuthProvider } from '@/features/auth/context/AuthProvider'
import { queryClient } from '@/lib/query-client'

/** Proveedores globales, en orden de dependencia: datos del servidor → sesión → notificaciones. */
export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
      <Toaster position="bottom-center" toastOptions={{ className: 'font-sans' }} />
    </QueryClientProvider>
  )
}
