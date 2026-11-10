import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'

import { env } from '@/config/env'

import { tokenStore } from './token-store'

/**
 * Cliente HTTP único para toda la app. Cada feature define sus llamadas en `features/<x>/api/`
 * usando este cliente; ningún componente llama a axios directamente.
 *
 * - Agrega `Authorization: Bearer <access>` a cada petición.
 * - Si la API responde 401, pide un access nuevo con la cookie (una sola vez aunque fallen varias
 *   peticiones a la vez) y reintenta. Si tampoco se puede, la sesión terminó: el token se borra y
 *   `AuthProvider` manda al login.
 */
export const api = axios.create({
  baseURL: env.apiUrl,
  withCredentials: true,
  headers: { Accept: 'application/json' },
})

const AUTH_PATHS = ['/auth/login/', '/auth/refresh/', '/auth/logout/']

let refreshing: Promise<string | null> | null = null

/** Pide un access token nuevo con la cookie httpOnly. Las llamadas simultáneas comparten la misma petición. */
export function refreshAccessToken(): Promise<string | null> {
  refreshing ??= axios
    .post<{ access: string }>(`${env.apiUrl}/auth/refresh/`, null, { withCredentials: true })
    .then(({ data }) => data.access)
    .catch(() => null)
    .then((token) => {
      tokenStore.set(token)
      return token
    })
    .finally(() => {
      refreshing = null
    })
  return refreshing
}

api.interceptors.request.use((config) => {
  const token = tokenStore.get()
  if (token) config.headers.set('Authorization', `Bearer ${token}`)
  return config
})

api.interceptors.response.use(undefined, async (error: AxiosError) => {
  const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined
  const isAuthCall = AUTH_PATHS.some((path) => original?.url?.endsWith(path))
  if (error.response?.status !== 401 || !original || original._retried || isAuthCall) {
    throw error
  }
  original._retried = true
  const token = await refreshAccessToken()
  if (!token) throw error
  original.headers.set('Authorization', `Bearer ${token}`)
  return api(original)
})
