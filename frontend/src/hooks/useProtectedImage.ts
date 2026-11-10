import { useEffect, useState } from 'react'

import { api } from '@/lib/api/client'
import { getProtectedObjectUrl } from '@/lib/media/protected-files'

type Status = 'idle' | 'loading' | 'ready' | 'error'

/**
 * Las fotos de usuarios se entregan por vistas que validan permisos (nunca por /media/), así que un
 * `<img src>` simple no lleva el token. Este hook las descarga con el cliente autenticado y devuelve
 * una URL local (`blob:`).
 * - `cache: true` (fotos de perfil): se guarda para toda la sesión y se comparte entre componentes.
 * - sin caché (fotos y videos de publicaciones): vive mientras el componente esté montado.
 */
export function useProtectedImage(url: string | null | undefined, { cache = false }: { cache?: boolean } = {}): { src: string | null; status: Status } {
  // Resultado de la última descarga terminada, con la URL a la que pertenece.
  const [result, setResult] = useState<{ url: string; src: string | null; ok: boolean } | null>(null)

  useEffect(() => {
    if (!url) return
    let objectUrl: string | null = null
    let cancelled = false
    const request = cache
      ? getProtectedObjectUrl(url)
      : api.get<Blob>(url, { baseURL: '', responseType: 'blob' }).then(({ data }) => (objectUrl = URL.createObjectURL(data)))
    request
      .then((src) => !cancelled && setResult({ url, src, ok: true }))
      .catch(() => !cancelled && setResult({ url, src: null, ok: false }))
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [url, cache])

  if (!url) return { src: null, status: 'idle' }
  if (result?.url !== url) return { src: null, status: 'loading' }
  return result.ok ? { src: result.src, status: 'ready' } : { src: null, status: 'error' }
}
