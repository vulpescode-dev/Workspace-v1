import type { ReactNode } from 'react'

import { Card } from './Card'

/** Tarjeta de la columna lateral de Inicio: título, acción opcional y contenido. */
export function Widget({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  return (
    <Card className="p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-sm font-bold text-slate-900">{title}</h2>
        {action}
      </div>
      {children}
    </Card>
  )
}
