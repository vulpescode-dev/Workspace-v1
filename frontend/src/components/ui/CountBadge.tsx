import { cn } from '@/lib/cn'

/** Globito con un número (avisos sin leer…). Desde 10 muestra «9+». Con 0 no se dibuja. */
export function CountBadge({ count, className }: { count: number; className?: string }) {
  if (count <= 0) return null
  return (
    <span
      aria-hidden
      className={cn(
        'pointer-events-none absolute grid h-[18px] min-w-[18px] place-items-center rounded-full bg-red-500 px-1',
        'text-[10px] leading-none font-bold text-white tabular-nums ring-2 ring-surface',
        className,
      )}
    >
      {count > 9 ? '9+' : count}
    </span>
  )
}
