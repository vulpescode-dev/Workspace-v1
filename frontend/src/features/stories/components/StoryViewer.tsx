import { useQueryClient } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, Eye, Pause, Play, Trash2, X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState, type ButtonHTMLAttributes, type CSSProperties } from 'react'
import { createPortal } from 'react-dom'
import { toast } from 'sonner'

import { useCan } from '@/features/accounts/hooks/useCan'
import { Spinner } from '@/components/ui/Spinner'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { useProtectedImage } from '@/hooks/useProtectedImage'
import { getErrorMessage } from '@/lib/api/errors'
import { cn } from '@/lib/cn'
import { formatRelative } from '@/lib/format'

import { storiesApi, storiesKeys } from '../api/stories.api'
import type { Story, StoryGroup } from '../types'
import { StoryViewersPanel } from './StoryViewersPanel'

const IMAGE_SECONDS = 5

interface StoryViewerProps {
  groups: StoryGroup[]
  startGroup: number
  onClose: () => void
}

/**
 * Visor a pantalla completa (como Instagram): barras de progreso arriba, tocar a la izquierda/derecha
 * para retroceder/avanzar, mantener presionado para pausar, Escape o ✕ para cerrar, flechas del teclado.
 * Una foto dura 5 s; un video, lo que dure. Al terminar los estados de una persona pasa a la siguiente.
 * Cambiar de estado no se anima (se hace muchas veces seguidas); solo la apertura (fundido 200 ms).
 */
export function StoryViewer({ groups, startGroup, onClose }: StoryViewerProps) {
  const can = useCan()
  const queryClient = useQueryClient()
  const [groupIndex, setGroupIndex] = useState(startGroup)
  const [storyIndex, setStoryIndex] = useState(() => firstUnseen(groups[startGroup]))
  const [paused, setPaused] = useState(false)
  const [showViewers, setShowViewers] = useState(false)
  const seenRef = useRef(new Set<number>())

  const group = groups[groupIndex]
  const story = group?.stories[storyIndex]
  // La barra empieza a llenarse cuando el archivo ya llegó (y, si es video, cuando se sabe cuánto dura).
  const media = useProtectedImage(story?.url)
  const [videoMeta, setVideoMeta] = useState<{ id: number; seconds: number; ratio: number | null } | null>(null)
  const meta = story && videoMeta?.id === story.id ? videoMeta : null
  const seconds = story?.kind === 'video' ? (meta?.seconds ?? null) : IMAGE_SECONDS
  // Proporción del marco: la de la foto (la manda el servidor) o la del video (al leer sus datos).
  const ratio = frameRatio(story?.kind === 'video' ? meta?.ratio : story?.width && story.height ? story.width / story.height : null)
  const running = Boolean(media.src && seconds)
  const isPaused = paused || showViewers

  const close = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: storiesKeys.tray() })   // los aros se actualizan al cerrar
    onClose()
  }, [onClose, queryClient])

  const next = useCallback(() => {
    if (storyIndex < group.stories.length - 1) return setStoryIndex(storyIndex + 1)
    if (groupIndex < groups.length - 1) {
      setGroupIndex(groupIndex + 1)
      setStoryIndex(firstUnseen(groups[groupIndex + 1]))
      return
    }
    close()
  }, [storyIndex, group, groupIndex, groups, close])

  const previous = useCallback(() => {
    if (storyIndex > 0) return setStoryIndex(storyIndex - 1)
    if (groupIndex > 0) {
      setGroupIndex(groupIndex - 1)
      setStoryIndex(groups[groupIndex - 1].stories.length - 1)
    }
  }, [storyIndex, groupIndex, groups])

  // Marcar como visto (una vez por estado y solo los ajenos).
  useEffect(() => {
    if (!story || group.is_mine || story.seen || seenRef.current.has(story.id)) return
    seenRef.current.add(story.id)
    void storiesApi.markSeen(story.id).catch(() => seenRef.current.delete(story.id))
  }, [story, group])

  // Teclado y bloqueo del scroll de la página mientras el visor está abierto.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') return showViewers ? setShowViewers(false) : close()
      if (event.key === 'ArrowRight') next()
      if (event.key === 'ArrowLeft') previous()
      if (event.key === ' ') {
        event.preventDefault()
        setPaused((value) => !value)
      }
    }
    document.addEventListener('keydown', onKeyDown)
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = overflow
    }
  }, [close, next, previous, showViewers])

  async function removeMine() {
    if (!story || !window.confirm('¿Eliminar este estado?')) return
    try {
      await storiesApi.remove(story.id)
      toast('Estado eliminado.')
      close()
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo eliminar.'))
    }
  }

  if (!group || !story) return null

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Estados de ${group.author.name}`}
      className="fixed inset-0 z-[60] grid place-items-center bg-slate-950 transition-opacity duration-200 ease-out starting:opacity-0"
    >
      {/* Teléfono: pantalla completa. Pantallas más anchas: el marco toma la proporción del estado (vertical
          como teléfono, horizontal a lo ancho) sin pasar de 92 % de alto ni de ancho. */}
      <div
        style={{ '--ratio': ratio } as CSSProperties}
        className="relative flex h-full max-h-dvh w-full flex-col overflow-hidden bg-black sm:aspect-(--ratio) sm:h-auto sm:max-h-[min(92dvh,52rem)] sm:w-[min(92dvw,calc(min(92dvh,52rem)*var(--ratio)))] sm:min-w-80 sm:rounded-2xl"
      >
        {/* Contenido + zonas táctiles: izquierda = anterior, derecha = siguiente, mantener = pausa. */}
        <StoryMedia
          key={story.id}
          story={story}
          src={media.src}
          failed={media.status === 'error'}
          paused={isPaused}
          onMeta={(value) => setVideoMeta({ id: story.id, ...value })}
          onEnded={next}
        />
        <div
          className="absolute inset-0 z-10 grid grid-cols-[1fr_2fr]"
          onPointerDown={() => setPaused(true)}
          onPointerUp={() => setPaused(false)}
          onPointerLeave={() => setPaused(false)}
        >
          <button type="button" aria-label="Estado anterior" onClick={previous} className="outline-none" />
          <button type="button" aria-label="Siguiente estado" onClick={next} className="outline-none" />
        </div>

        {/* Arriba: barras de progreso, autor y controles (encima de las zonas táctiles). */}
        <div className="absolute inset-x-0 top-0 z-20 bg-gradient-to-b from-black/60 to-transparent px-3 pt-[calc(0.75rem+env(safe-area-inset-top))] pb-8">
          <div className="flex gap-1">
            {group.stories.map((item, index) => (
              <span key={item.id} className="h-[3px] flex-1 overflow-hidden rounded-full bg-white/30">
                <span
                  className={cn('story-progress block h-full origin-left bg-white', index < storyIndex ? 'scale-x-100' : 'scale-x-0')}
                  style={index === storyIndex && running ? progressStyle(seconds!, isPaused) : undefined}
                  // Las fotos avanzan al llenarse la barra; los videos, cuando terminan de reproducirse.
                  onAnimationEnd={index === storyIndex && story.kind === 'image' ? next : undefined}
                />
              </span>
            ))}
          </div>
          <div className="mt-3 flex items-center gap-2.5 text-white">
            <UserAvatar user={group.author} size="sm" />
            <p className="min-w-0 flex-1 truncate text-sm font-semibold">
              {group.is_mine ? 'Tu estado' : group.author.name}
              <span className="ml-2 font-normal text-white/70">{formatRelative(story.created_at)}</span>
            </p>
            <IconButton label={paused ? 'Reanudar' : 'Pausar'} onClick={() => setPaused((value) => !value)}>
              {paused ? <Play className="size-5" /> : <Pause className="size-5" />}
            </IconButton>
            {group.is_mine && can('social.stories.delete') && (
              <IconButton label="Eliminar estado" onClick={() => void removeMine()}>
                <Trash2 className="size-5" />
              </IconButton>
            )}
            <IconButton label="Cerrar" onClick={close}>
              <X className="size-6" />
            </IconButton>
          </div>
        </div>

        {/* Mis estados: «Visto por N» abajo. */}
        {group.is_mine && story.views_count !== null && (
          <div className="absolute inset-x-0 bottom-0 z-20 flex justify-center bg-gradient-to-t from-black/60 to-transparent px-3 pt-10 pb-[calc(1rem+env(safe-area-inset-bottom))]">
            <button
              type="button"
              onClick={() => setShowViewers(true)}
              className="pressable flex items-center gap-2 rounded-full bg-white/15 px-4 py-2 text-sm font-semibold text-white backdrop-blur-sm hover:bg-white/25"
            >
              <Eye className="size-4" aria-hidden /> Visto por {story.views_count}
            </button>
          </div>
        )}
        {showViewers && group.is_mine && (
          <StoryViewersPanel key={story.id} storyId={story.id} count={story.views_count ?? 0} onClose={() => setShowViewers(false)} />
        )}
      </div>

      {/* Escritorio: flechas a los lados del visor. */}
      <div className="pointer-events-none absolute inset-x-0 top-1/2 hidden -translate-y-1/2 justify-between px-6 sm:flex">
        <IconButton label="Anterior" onClick={previous} className="pointer-events-auto bg-white/15" disabled={groupIndex === 0 && storyIndex === 0}>
          <ChevronLeft className="size-6" />
        </IconButton>
        <IconButton label="Siguiente" onClick={next} className="pointer-events-auto bg-white/15">
          <ChevronRight className="size-6" />
        </IconButton>
      </div>
    </div>,
    document.body,
  )
}

/** Proporción del marco en pantallas anchas: la del estado, entre 9:16 (vertical) y 2:1 (panorámica). */
function frameRatio(value: number | null | undefined) {
  if (!value) return 9 / 16
  return Math.min(Math.max(value, 9 / 16), 2)
}

/** Abre a la persona en su primer estado sin ver (o en el primero si ya vio todos). */
function firstUnseen(group: StoryGroup | undefined) {
  if (!group) return 0
  const index = group.stories.findIndex((story) => !story.seen)
  return index === -1 ? 0 : index
}

/** La barra del estado actual se llena con una animación CSS (solo transform: barata); pausar la congela. */
function progressStyle(seconds: number, paused: boolean) {
  // --story-seconds: con «reducir movimiento» la duración global se anula; esta barra es tiempo, no adorno.
  return { '--story-seconds': `${seconds}s`, animation: `story-progress ${seconds}s linear forwards`, animationPlayState: paused ? 'paused' : 'running' } as CSSProperties
}

interface StoryMediaProps {
  story: Story
  src: string | null
  failed: boolean
  paused: boolean
  onMeta: (meta: { seconds: number; ratio: number | null }) => void
  onEnded: () => void
}

function StoryMedia({ story, src, failed, paused, onMeta, onEnded }: StoryMediaProps) {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return
    if (paused) video.pause()
    else void video.play().catch(() => undefined)
  }, [paused, src])

  if (failed) return <p className="m-auto px-6 text-center text-sm text-white/70">No se pudo cargar este estado.</p>
  if (!src) return <Spinner className="m-auto size-8 text-white" label="Cargando estado" />
  if (story.kind === 'video') {
    return (
      <video
        ref={videoRef}
        src={src}
        autoPlay
        playsInline
        onLoadedMetadata={({ currentTarget: video }) =>
          onMeta({ seconds: video.duration || IMAGE_SECONDS, ratio: video.videoWidth && video.videoHeight ? video.videoWidth / video.videoHeight : null })
        }
        onEnded={onEnded}
        className="m-auto max-h-full w-full object-contain"
      />
    )
  }
  return <img src={src} alt="Estado" className="m-auto max-h-full w-full object-contain" />
}

function IconButton({ label, className, children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={cn('pressable grid size-10 shrink-0 place-items-center rounded-full text-white hover:bg-white/15 disabled:opacity-30', className)}
      {...props}
    >
      {children}
    </button>
  )
}
