import { cn } from '@/lib/cn'

const sizes = { sm: 'size-8 text-xs', md: 'size-10 text-sm', lg: 'size-14 text-lg', xl: 'size-28 text-3xl sm:size-36 sm:text-4xl' } as const

interface AvatarProps {
  /** URL ya lista para `<img>` (p. ej. de `useProtectedImage`). Sin ella se muestran las iniciales. */
  src?: string | null
  initials: string
  name: string
  size?: keyof typeof sizes
  className?: string
}

/** Foto de una persona o sus iniciales. Componente visual puro: no pide datos. */
export function Avatar({ src, initials, name, size = 'md', className }: AvatarProps) {
  return (
    <span className={cn('relative inline-grid shrink-0 place-items-center overflow-hidden rounded-full bg-brand-100 font-bold text-brand-700', sizes[size], className)}>
      {src ? <img src={src} alt={name} className="size-full object-cover" /> : <span aria-label={name}>{initials}</span>}
    </span>
  )
}
