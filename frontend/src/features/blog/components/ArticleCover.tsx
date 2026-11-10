import { Newspaper } from 'lucide-react'

import { useProtectedImage } from '@/hooks/useProtectedImage'
import { cn } from '@/lib/cn'

/**
 * Portada de un artículo (16:9). Se descarga con sesión; mientras carga, o si no tiene, un degradado de
 * marca con el ícono de Noticias para que la cuadrícula no quede con huecos.
 */
export function ArticleCover({ url, src: localSrc, className }: { url?: string; src?: string | null; className?: string }) {
  const { src: remoteSrc, status } = useProtectedImage(localSrc ? null : url)
  const src = localSrc ?? remoteSrc
  return (
    <div className={cn('relative aspect-video overflow-hidden bg-gradient-to-br from-brand-50 to-brand-100', className)}>
      {src ? (
        <img src={src} alt="" className="size-full object-cover transition-opacity duration-300 starting:opacity-0" />
      ) : (
        <Newspaper className={cn('absolute top-1/2 left-1/2 size-10 -translate-1/2 text-brand-300', status === 'loading' && 'animate-pulse')} aria-hidden />
      )}
    </div>
  )
}
