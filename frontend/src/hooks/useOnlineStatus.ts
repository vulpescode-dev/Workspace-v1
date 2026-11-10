import { useSyncExternalStore } from 'react'

/** ¿El navegador tiene red? Cambia al perder o recuperar la conexión (eventos `online`/`offline`). */
export function useOnlineStatus() {
  return useSyncExternalStore(
    (onChange) => {
      window.addEventListener('online', onChange)
      window.addEventListener('offline', onChange)
      return () => {
        window.removeEventListener('online', onChange)
        window.removeEventListener('offline', onChange)
      }
    },
    () => navigator.onLine,
  )
}
