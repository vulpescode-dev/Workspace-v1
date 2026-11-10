import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** Une clases de Tailwind resolviendo conflictos: `cn('px-4', isWide && 'px-8')` → `px-8`. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
