import { Hammer } from 'lucide-react'
import { Link } from 'react-router'

import { EmptyState } from '@/components/feedback/EmptyState'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card } from '@/components/ui/Card'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'

/** Sección que todavía no tiene pantalla en React: mismo encabezado que las demás y un aviso honesto. */
export function ComingSoonPage({ title }: { title: string }) {
  useDocumentTitle(title)
  return (
    <>
      <PageHeader title={title} />
      <Card>
        <EmptyState
          icon={Hammer}
          title="Próximamente"
          description="Esta sección se está reconstruyendo y llegará en una próxima entrega."
          action={
            <Link to="/" className="pressable rounded-xl px-4 py-2.5 text-sm font-semibold text-brand-600 hover:bg-brand-50">
              Volver al inicio
            </Link>
          }
        />
      </Card>
    </>
  )
}
