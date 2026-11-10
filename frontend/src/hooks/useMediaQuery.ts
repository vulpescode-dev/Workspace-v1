import { useSyncExternalStore } from 'react'

/** ¿Cumple la media query ahora? Se actualiza al girar el teléfono o cambiar el tamaño de la ventana. */
export function useMediaQuery(query: string) {
  return useSyncExternalStore(
    (onChange) => {
      const list = window.matchMedia(query)
      list.addEventListener('change', onChange)
      return () => list.removeEventListener('change', onChange)
    },
    () => window.matchMedia(query).matches,
  )
}
