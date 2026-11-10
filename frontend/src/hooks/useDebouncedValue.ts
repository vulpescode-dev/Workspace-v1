import { useEffect, useState } from 'react'

/** El valor, pero solo cuando deja de cambiar `delay` ms (búsquedas mientras se escribe). */
export function useDebouncedValue<T>(value: T, delay = 300) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay)
    return () => window.clearTimeout(timer)
  }, [value, delay])
  return debounced
}
