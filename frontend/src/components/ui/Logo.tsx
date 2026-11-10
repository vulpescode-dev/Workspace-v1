import { env } from '@/config/env'
import { cn } from '@/lib/cn'

/** Marca del proyecto (ícono + nombre desde VITE_PROJECT_NAME). */
export function Logo({ className, inverted = false }: { className?: string; inverted?: boolean }) {
  return (
    <span className={cn('inline-flex items-center gap-2 font-display text-lg font-extrabold tracking-tight', inverted ? 'text-white' : 'text-slate-900', className)}>
      <img src="/icons/favicon-32.png" alt="" className="size-7 rounded-lg" />
      {env.projectName}
    </span>
  )
}
