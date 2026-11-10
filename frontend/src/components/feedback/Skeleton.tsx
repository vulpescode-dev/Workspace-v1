import type { HTMLAttributes, ReactNode } from 'react'

import { cn } from '@/lib/cn'

/**
 * Bloque gris que ocupa el lugar de algo que aún carga (texto, foto, botón). Cada pantalla arma su
 * propio esqueleto con la MISMA forma que el contenido real, para que nada brinque al llegar los datos.
 * Pulsa suave (opacidad); con «reducir movimiento» queda quieto.
 */
export function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div aria-hidden className={cn('animate-pulse rounded-lg bg-slate-200/80 motion-reduce:animate-none', className)} {...props} />
}

/** Contenedor para un grupo de esqueletos: lo anuncia una sola vez a lectores de pantalla. */
export function SkeletonGroup({ label = 'Cargando', className, children }: { label?: string; className?: string; children: ReactNode }) {
  return (
    <div role="status" aria-busy="true" aria-label={label} className={className}>
      {children}
    </div>
  )
}
