import { ChevronLeft, ChevronRight, X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState, type ButtonHTMLAttributes } from 'react'
import { createPortal } from 'react-dom'

import { Spinner } from '@/components/ui/Spinner'
import { useProtectedImage } from '@/hooks/useProtectedImage'
import { cn } from '@/lib/cn'

import type { PostAttachment } from '../types'

/** Lo único que necesita la galería: también la usan las fotos del Marketplace. */
export type GalleryItemData = Pick<PostAttachment, 'id' | 'kind' | 'url'>

interface PostGalleryProps {
  attachments: GalleryItemData[]
  startIndex: number
  onClose: () => void
}

/**
 * Galería a pantalla completa de una publicación: solo sus fotos y videos, en orden. Flechas (o ← →),
 * deslizar con el dedo, contador «2 / 5» y Escape o ✕ para cerrar. Abrir se anima (fundido 200 ms);
 * pasar de una foto a otra no (se hace muchas veces seguidas).
 */
export function PostGallery({ attachments, startIndex, onClose }: PostGalleryProps) {
  const [index, setIndex] = useState(startIndex)
  const swipeStart = useRef<number | null>(null)
  const total = attachments.length
  const current = attachments[index]

  const previous = useCallback(() => setIndex((value) => Math.max(0, value - 1)), [])
  const next = useCallback(() => setIndex((value) => Math.min(total - 1, value + 1)), [total])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
      if (event.key === 'ArrowLeft') previous()
      if (event.key === 'ArrowRight') next()
    }
    document.addEventListener('keydown', onKeyDown)
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = overflow
    }
  }, [onClose, previous, next])

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Foto ${index + 1} de ${total}`}
      className="fixed inset-0 z-[60] flex flex-col bg-slate-950/95 transition-opacity duration-200 ease-out starting:opacity-0"
      onPointerDown={(event) => (swipeStart.current = event.clientX)}
      onPointerUp={(event) => {
        if (swipeStart.current === null) return
        const distance = event.clientX - swipeStart.current
        swipeStart.current = null
        if (distance > 60) previous()
        if (distance < -60) next()
      }}
    >
      <div className="flex items-center justify-between px-4 pt-[calc(0.75rem+env(safe-area-inset-top))] pb-2 text-white">
        <span className="text-sm font-semibold tabular-nums">{total > 1 ? `${index + 1} / ${total}` : ''}</span>
        <GalleryButton label="Cerrar" onClick={onClose}>
          <X className="size-6" />
        </GalleryButton>
      </div>

      <div className="relative flex min-h-0 flex-1 items-center justify-center px-2 pb-[calc(1rem+env(safe-area-inset-bottom))] sm:px-16">
        <GalleryItem key={current.id} attachment={current} />
        {total > 1 && (
          <>
            <GalleryButton label="Anterior" onClick={previous} disabled={index === 0} className="absolute left-2 hidden sm:grid">
              <ChevronLeft className="size-7" />
            </GalleryButton>
            <GalleryButton label="Siguiente" onClick={next} disabled={index === total - 1} className="absolute right-2 hidden sm:grid">
              <ChevronRight className="size-7" />
            </GalleryButton>
          </>
        )}
      </div>
    </div>,
    document.body,
  )
}

function GalleryItem({ attachment }: { attachment: GalleryItemData }) {
  const { src, status } = useProtectedImage(attachment.url)
  if (status === 'error') return <p className="text-sm text-white/70">No se pudo cargar.</p>
  if (!src) return <Spinner className="size-8 text-white" label="Cargando" />
  if (attachment.kind === 'video') {
    return <video src={src} controls autoPlay playsInline className="max-h-full max-w-full rounded-lg" onPointerDown={(event) => event.stopPropagation()} />
  }
  return <img src={src} alt="Foto de la publicación" className="max-h-full max-w-full rounded-lg object-contain select-none" draggable={false} />
}

function GalleryButton({ label, className, children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onPointerDown={(event) => event.stopPropagation()}
      className={cn('pressable grid size-11 place-items-center rounded-full bg-white/10 text-white hover:bg-white/20 disabled:opacity-30', className)}
      {...props}
    >
      {children}
    </button>
  )
}
