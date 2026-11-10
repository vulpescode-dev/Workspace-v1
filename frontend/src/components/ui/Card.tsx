import type { HTMLAttributes } from 'react'

import { cn } from '@/lib/cn'

/** Superficie blanca con borde sutil: la base de tarjetas de posts, avisos, documentos… */
export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('rounded-2xl border border-slate-200/70 bg-surface shadow-sm shadow-slate-900/[0.03]', className)} {...props} />
}
