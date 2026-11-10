import { Lock } from 'lucide-react'
import { Link, Outlet } from 'react-router'

import { EmptyState } from '@/components/feedback/EmptyState'
import { Skeleton } from '@/components/feedback/Skeleton'
import { Card } from '@/components/ui/Card'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'

import type { Section } from '../access'
import { useSectionAccess } from '../hooks/useCan'

/**
 * Guardia de ruta por sección (permisos de negocio): sin acceso muestra un aviso dentro del armazón en vez
 * de una página que fallaría con 403. Mientras llegan mis permisos, un esqueleto.
 */
export function RequireAccess({ section }: { section: Section }) {
  const { ready, canSee } = useSectionAccess()
  if (!ready) return <Skeleton className="h-64 w-full rounded-2xl" />
  return canSee(section) ? <Outlet /> : <NoAccess />
}

/** Aviso «sin acceso» dentro del armazón (también para pestañas con su propio permiso). */
export function NoAccess() {
  useDocumentTitle('Sin acceso')
  return (
    <Card>
      <EmptyState
        icon={Lock}
        title="No tienes acceso a esta sección"
        description="Tus roles no incluyen el permiso para verla. Si la necesitas para tu trabajo, pide a Soporte TI que te lo asigne."
        action={
          <Link to="/" className="pressable rounded-xl bg-brand-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-600">
            Ir al inicio
          </Link>
        }
      />
    </Card>
  )
}
