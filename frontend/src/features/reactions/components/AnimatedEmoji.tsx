import type { AnimationItem } from 'lottie-web'
import { useEffect, useRef, useState } from 'react'

import { cn } from '@/lib/cn'

import type { Emoji } from '../types'
import { playLottie } from '../utils/lottie'

interface AnimatedEmojiProps {
  emoji?: Emoji
  /** `false` = SVG quieto. `'once'` = una vez y vuelve al SVG. `'loop'` = mientras siga activo. */
  play: false | 'once' | 'loop'
  /** Cambia este número para volver a reproducir `'once'` (p. ej. cada vez que reaccionas). */
  replayKey?: number
  className?: string
  fallback?: string
}

/**
 * Emoji del catálogo: SVG estático siempre (ligero) y, encima, la animación Lottie solo cuando se pide.
 * Así el feed nunca anima en bucle: se anima el que tocas, el que señalas o el que acabas de elegir.
 */
export function AnimatedEmoji({ emoji, play, replayKey = 0, className, fallback }: AnimatedEmojiProps) {
  const containerRef = useRef<HTMLSpanElement>(null)
  const [animating, setAnimating] = useState(false)

  useEffect(() => {
    const container = containerRef.current
    if (!play || !emoji || !container) return
    let animation: AnimationItem | null = null
    const controller = new AbortController()
    void playLottie(container, emoji.lottie_url, play === 'loop', controller.signal)
      .then((item) => {
        if (controller.signal.aborted) return item?.destroy()
        animation = item
        if (!item) return
        // El SVG quieto se oculta cuando la animación ya dibujó su primer cuadro (si no, se ve un hueco).
        if (item.isLoaded) setAnimating(true)
        else item.addEventListener('DOMLoaded', () => setAnimating(true))
        if (play === 'once') item.addEventListener('complete', () => {
          item.destroy()
          setAnimating(false)
        })
      })
      .catch(() => undefined)   // sin animación, queda el SVG: nunca un error visible por esto
    return () => {
      controller.abort()
      animation?.destroy()
      setAnimating(false)
    }
  }, [play, emoji, replayKey])

  return (
    <span className={cn('relative inline-block shrink-0', className)}>
      {emoji ? (
        <img
          src={emoji.svg_url}
          alt={emoji.label}
          draggable={false}
          loading="lazy"
          decoding="async"
          className={cn('size-full', animating && 'invisible')}
        />
      ) : (
        <span className="grid size-full place-items-center leading-none">{fallback ?? '🙂'}</span>
      )}
      <span ref={containerRef} aria-hidden className="pointer-events-none absolute inset-0 [&>svg]:!size-full" />
    </span>
  )
}
