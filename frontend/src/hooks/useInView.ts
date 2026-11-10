import { useEffect, useRef, useState } from 'react'

/** ¿El elemento está en pantalla (o a `margin` de estarlo)? Útil para animar o cargar solo lo visible. */
export function useInView<T extends Element>(margin = '0px') {
  const ref = useRef<T>(null)
  const [inView, setInView] = useState(false)

  useEffect(() => {
    const element = ref.current
    if (!element) return
    const observer = new IntersectionObserver(([entry]) => setInView(entry.isIntersecting), { rootMargin: margin })
    observer.observe(element)
    return () => observer.disconnect()
  }, [margin])

  return [ref, inView] as const
}
