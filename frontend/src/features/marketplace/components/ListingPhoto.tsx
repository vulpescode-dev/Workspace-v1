import { ImageOff, ShoppingBag } from 'lucide-react'

import { useProtectedImage } from '@/hooks/useProtectedImage'
import { cn } from '@/lib/cn'

/** Foto de un anuncio (con sesión). Sin foto: bolsa gris para que la cuadrícula no tenga huecos. */
export function ListingPhoto({ url, alt = '', className }: { url?: string; alt?: string; className?: string }) {
  const { src, status } = useProtectedImage(url)
  return (
    <div className={cn('relative overflow-hidden bg-slate-100', className)}>
      {src ? (
        <img src={src} alt={alt} className="size-full object-cover transition-opacity duration-300 starting:opacity-0" />
      ) : (
        <span className={cn('absolute inset-0 grid place-items-center text-slate-300', status === 'loading' && 'animate-pulse')}>
          {status === 'error' ? <ImageOff className="size-8" aria-hidden /> : <ShoppingBag className="size-10" aria-hidden />}
        </span>
      )}
    </div>
  )
}
