import type { ReactNode } from 'react'

import { AnimatedEmoji } from '@/features/reactions/components/AnimatedEmoji'
import type { Emoji } from '@/features/reactions/types'

interface ErrorSceneProps {
  /** Emoji protagonista (animado en bucle). */
  emoji: Emoji
  /** Uno o dos emojis pequeños que flotan alrededor del protagonista. */
  companions?: [Emoji] | [Emoji, Emoji]
  /** Etiqueta corta arriba del título: «Error 404», «Sin conexión»… */
  code: string
  title: string
  description: string
  actions?: ReactNode
  /** Extra debajo de las acciones (p. ej. el detalle técnico en desarrollo). */
  children?: ReactNode
}

/**
 * Pantalla de error con personalidad, a pantalla completa como el login (sin encabezado ni tarjeta):
 * un emoji animado grande, acompañantes que flotan y un mensaje claro de qué pasó y qué hacer,
 * todo centrado en ambos ejes. Con «reducir movimiento» los emojis quedan quietos.
 */
export function ErrorScene({ emoji, companions, code, title, description, actions, children }: ErrorSceneProps) {
  const [left, right] = companions ?? []
  return (
    <main className="grid min-h-dvh place-items-center px-4 py-10 sm:px-6">
      <div className="grid w-full max-w-xl animate-enter justify-items-center gap-5 text-center">
        <div className="relative size-36 sm:size-44">
          <div aria-hidden className="absolute inset-3 rounded-full bg-gradient-to-br from-brand-100 to-accent-100 blur-2xl" />
          <AnimatedEmoji emoji={emoji} play="loop" className="relative size-full drop-shadow-sm" />
          {left && <AnimatedEmoji emoji={left} play="loop" className="ws-float absolute -top-2 -left-8 size-11 -rotate-12 sm:-left-10 sm:size-12" />}
          {right && <AnimatedEmoji emoji={right} play="loop" className="ws-float absolute -right-7 bottom-1 size-10 rotate-12 [animation-delay:-1.4s] sm:-right-9 sm:size-11" />}
        </div>

        <div className="grid justify-items-center gap-2">
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold tracking-wide text-slate-500 uppercase tabular-nums">{code}</span>
          <h1 className="font-display text-2xl font-extrabold text-balance text-slate-900 sm:text-3xl">{title}</h1>
          <p className="max-w-md text-sm text-pretty text-slate-500 sm:text-base">{description}</p>
        </div>

        {actions && <div className="flex flex-wrap justify-center gap-2 pt-1">{actions}</div>}
        {children}
      </div>
    </main>
  )
}
