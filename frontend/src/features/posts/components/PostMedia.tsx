import { Play } from 'lucide-react'
import { useState } from 'react'

import { ProtectedImage } from '@/components/media/ProtectedImage'
import { Spinner } from '@/components/ui/Spinner'
import { useProtectedImage } from '@/hooks/useProtectedImage'
import { cn } from '@/lib/cn'

import type { PostAttachment } from '../types'
import { PostGallery } from './PostGallery'

const MAX_TILES = 4

/**
 * Fotos y videos de una publicación en mosaico: 1 a lo ancho, 2 lado a lado, 3 (una grande + dos),
 * 4 o más en 2×2 con «+N» en la última. Tocar una foto (o el «+N») abre la galería a pantalla completa.
 */
export function PostMedia({ attachments }: { attachments: PostAttachment[] }) {
  const [galleryAt, setGalleryAt] = useState<number | null>(null)
  const tiles = attachments.slice(0, MAX_TILES)
  const extra = attachments.length - tiles.length
  const single = tiles.length === 1

  return (
    <div className={cn('mt-3 grid gap-0.5 overflow-hidden bg-slate-100', !single && 'aspect-[4/3] grid-cols-2', tiles.length >= 3 && 'grid-rows-2')}>
      {tiles.map((attachment, index) => (
        <div
          key={attachment.id}
          className={cn('relative min-h-0 overflow-hidden', tiles.length === 3 && index === 0 && 'row-span-2')}
          style={single ? { aspectRatio: aspectOf(attachment) } : undefined}
        >
          {attachment.kind === 'video' ? (
            <PostVideo attachment={attachment} />
          ) : (
            <button type="button" onClick={() => setGalleryAt(index)} aria-label={`Ver foto ${index + 1} de ${attachments.length}`} className="block size-full cursor-zoom-in">
              <ProtectedImage url={attachment.url} alt="Foto de la publicación" className="size-full" />
            </button>
          )}
          {index === tiles.length - 1 && extra > 0 && (
            <button
              type="button"
              onClick={() => setGalleryAt(index)}
              aria-label={`Ver ${extra} fotos más`}
              className="absolute inset-0 grid place-items-center bg-slate-950/50 text-2xl font-bold text-white"
            >
              +{extra}
            </button>
          )}
        </div>
      ))}
      {galleryAt !== null && <PostGallery attachments={attachments} startIndex={galleryAt} onClose={() => setGalleryAt(null)} />}
    </div>
  )
}

/** Proporción de una sola foto, acotada para que una muy alta no ocupe toda la pantalla. */
function aspectOf({ width, height }: PostAttachment) {
  if (!width || !height) return '4 / 3'
  return String(Math.min(Math.max(width / height, 4 / 5), 2))
}

/**
 * Los videos pesan mucho: no se descargan hasta que la persona toca «reproducir» (ahorra datos en
 * el feed). Luego se reproducen con los controles del navegador.
 */
function PostVideo({ attachment }: { attachment: PostAttachment }) {
  const [requested, setRequested] = useState(false)
  const { src, status } = useProtectedImage(requested ? attachment.url : null)

  if (src) return <video src={src} controls autoPlay playsInline className="size-full bg-black object-contain" />
  return (
    <button
      type="button"
      onClick={() => setRequested(true)}
      aria-label="Reproducir video"
      className="group grid size-full min-h-48 place-items-center bg-slate-900 text-white"
    >
      <span className="pressable grid size-14 place-items-center rounded-full bg-white/20 backdrop-blur-sm transition-colors duration-150 group-hover:bg-white/30">
        {status === 'loading' ? <Spinner className="size-6" label="Cargando video" /> : <Play className="ml-0.5 size-6 fill-current" aria-hidden />}
      </span>
    </button>
  )
}
