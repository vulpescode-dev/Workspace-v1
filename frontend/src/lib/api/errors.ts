import { isAxiosError } from 'axios'

/** Mensaje legible de un error de la API (`{"detail": "..."}` o errores por campo de DRF). */
export function getErrorMessage(error: unknown, fallback = 'Algo salió mal. Inténtalo de nuevo.'): string {
  if (isAxiosError(error)) {
    if (!error.response) return 'No hay conexión con el servidor.'
    if (error.response.status === 429) return 'Demasiados intentos. Espera un minuto y vuelve a intentar.'
    const data = error.response.data as Record<string, unknown> | undefined
    if (typeof data?.detail === 'string') return data.detail
    const first = data && Object.values(data)[0]
    if (Array.isArray(first) && typeof first[0] === 'string') return first[0]
  }
  return fallback
}
