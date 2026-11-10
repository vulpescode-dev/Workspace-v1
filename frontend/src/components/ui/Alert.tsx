import { CircleAlert, Info } from 'lucide-react'
import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'

const tones = {
  error: { box: 'border-red-200 bg-red-50 text-red-800', Icon: CircleAlert },
  info: { box: 'border-brand-200 bg-brand-50 text-brand-800', Icon: Info },
} as const

/** Mensaje dentro de la página (errores de formulario, avisos). Para mensajes pasajeros usar `toast()`. */
export function Alert({ tone = 'info', children, className }: { tone?: keyof typeof tones; children: ReactNode; className?: string }) {
  const { box, Icon } = tones[tone]
  return (
    <div role={tone === 'error' ? 'alert' : 'status'} className={cn('flex items-start gap-2.5 rounded-xl border px-3.5 py-3 text-sm animate-enter', box, className)}>
      <Icon className="mt-px size-4 shrink-0" aria-hidden />
      <div>{children}</div>
    </div>
  )
}
