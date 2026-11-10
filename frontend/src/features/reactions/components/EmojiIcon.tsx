import { cn } from '@/lib/cn'

import type { Emoji } from '../types'

/** Emoji del catálogo (SVG de Noto). Sin el catálogo cargado, cae al carácter Unicode. */
export function EmojiIcon({ emoji, fallback, className }: { emoji?: Emoji; fallback?: string; className?: string }) {
  if (!emoji) return <span className={cn('inline-block text-center leading-none', className)}>{fallback ?? '🙂'}</span>
  return <img src={emoji.svg_url} alt={emoji.label} className={cn('inline-block', className)} loading="lazy" decoding="async" draggable={false} />
}
