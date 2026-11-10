import { createElement } from 'react'

import { cn } from '@/lib/cn'

import { kindOf } from '../utils'

/** Ícono y color según el tipo de archivo (como en un explorador de archivos): se reconoce de un vistazo. */
export function FileTypeIcon({ contentType, name, className }: { contentType?: string; name?: string; className?: string }) {
  const kind = kindOf(contentType, name)
  return (
    <span className={cn('grid size-11 shrink-0 place-items-center rounded-xl', kind.tone, className)}>
      {createElement(kind.icon, { className: 'size-5', 'aria-hidden': true })}
    </span>
  )
}
