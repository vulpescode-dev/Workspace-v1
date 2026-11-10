import { ImageOff } from 'lucide-react'

import { Skeleton } from '@/components/feedback/Skeleton'
import { useProtectedImage } from '@/hooks/useProtectedImage'
import { cn } from '@/lib/cn'

interface ProtectedImageProps {
  /** Ruta de la API que entrega el archivo (p. ej. `/api/social/attachments/12/file/`). */
  url: string
  alt: string
  className?: string
}

/** Imagen que pide sesión: esqueleto mientras se descarga, la foto al llegar y un aviso si falla. */
export function ProtectedImage({ url, alt, className }: ProtectedImageProps) {
  const { src, status } = useProtectedImage(url)
  if (status === 'error') {
    return (
      <div className={cn('grid place-items-center bg-slate-100 text-slate-400', className)}>
        <ImageOff className="size-6" aria-label="No se pudo cargar la imagen" />
      </div>
    )
  }
  if (!src) return <Skeleton className={cn('rounded-none', className)} />
  return <img src={src} alt={alt} className={cn('object-cover', className)} decoding="async" />
}
