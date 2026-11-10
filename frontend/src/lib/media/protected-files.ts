import { api } from '@/lib/api/client'

/**
 * Archivos que piden sesión (fotos de perfil): se descargan con el token y quedan como URL local
 * (`blob:`) en memoria durante la sesión, para no volver a pedir la misma foto cada vez que aparece
 * (directorio, organigrama, comentarios…). Las URLs de la API llevan `?v=`: si alguien cambia su foto,
 * la URL cambia y se descarga la nueva.
 */
const cache = new Map<string, Promise<string>>()

export function getProtectedObjectUrl(url: string): Promise<string> {
  let entry = cache.get(url)
  if (!entry) {
    // La ruta de la API ya incluye /api; se pide relativa a la raíz.
    entry = api.get<Blob>(url, { baseURL: '', responseType: 'blob' }).then(({ data }) => URL.createObjectURL(data))
    entry.catch(() => cache.delete(url))   // si falla, se reintenta la próxima vez
    cache.set(url, entry)
  }
  return entry
}

/** Al cerrar sesión: libera las fotos de la persona anterior. */
export function clearProtectedFiles() {
  cache.forEach((entry) => void entry.then((objectUrl) => URL.revokeObjectURL(objectUrl)).catch(() => undefined))
  cache.clear()
}
