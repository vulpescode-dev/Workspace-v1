import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'

export type RingState = 'unseen' | 'seen' | 'none'

/**
 * Aro alrededor de la foto, como Instagram: degradado de marca (azul → amarillo) si hay estados sin ver,
 * gris si ya se vieron todos, nada si la persona no tiene estados. Entre aro y foto queda un borde
 * blanco para que el aro se lea aunque la foto sea del mismo color.
 */
export function StoryRing({ state, children, className }: { state: RingState; children: ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        'inline-grid rounded-full p-[3px]',
        state === 'unseen' && 'bg-[conic-gradient(from_210deg,var(--color-accent-400),var(--color-brand-400),var(--color-brand-600),var(--color-accent-400))]',
        state === 'seen' && 'bg-slate-300',
        className,
      )}
    >
      <span className="inline-grid rounded-full bg-surface p-[2px]">{children}</span>
    </span>
  )
}
