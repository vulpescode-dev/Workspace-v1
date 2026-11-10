import { Link, useNavigate } from 'react-router'

import { ERROR_EMOJIS } from '@/components/feedback/error-emojis'
import { ErrorScene } from '@/components/feedback/ErrorScene'
import { Button } from '@/components/ui/Button'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'

/** 404: la ruta no existe (o el enlace está mal escrito). */
export function NotFoundPage() {
  useDocumentTitle('Página no encontrada')
  const navigate = useNavigate()
  return (
    <ErrorScene
      emoji={ERROR_EMOJIS.thinking}
      companions={[ERROR_EMOJIS.question, ERROR_EMOJIS.monkey]}
      code="Error 404"
      title="Esta página se nos perdió"
      description="Buscamos por todos lados y no la encontramos. Puede que el enlace esté mal escrito o que la página ya no exista."
      actions={
        <>
        <Button variant="ghost" onClick={() => navigate(-1)}>Regresar</Button>
        <Link to="/" className="pressable inline-flex h-11 items-center rounded-xl bg-brand-500 px-4 text-sm font-semibold text-white shadow-sm shadow-brand-900/10 hover:bg-brand-600">
          Ir al inicio
        </Link>
        </>
      }
    />
  )
}
