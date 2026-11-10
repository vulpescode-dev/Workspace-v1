import { isRouteErrorResponse, useRouteError } from 'react-router'

import { ERROR_EMOJIS } from '@/components/feedback/error-emojis'
import { ErrorScene } from '@/components/feedback/ErrorScene'
import { OfflineScreen } from '@/components/feedback/OfflineScreen'
import { Button } from '@/components/ui/Button'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'

import { NotFoundPage } from './NotFoundPage'

/** 500: algo falló de nuestro lado. Recargar suele bastar; si no, ir al inicio. */
export function ServerErrorPage({ detail }: { detail?: string }) {
  useDocumentTitle('Algo salió mal')
  return (
    <ErrorScene
      emoji={ERROR_EMOJIS.dizzy}
      companions={[ERROR_EMOJIS.fire, ERROR_EMOJIS.bandage]}
      code="Error 500"
      title="Ups, algo se nos rompió"
      description="No es tu culpa: tuvimos un problema de nuestro lado. Recarga la página; si sigue pasando, avisa a Soporte TI."
      actions={
        <>
          <Button variant="ghost" onClick={() => window.location.assign('/')}>Ir al inicio</Button>
          <Button onClick={() => window.location.reload()}>Recargar</Button>
        </>
      }
    >
      {import.meta.env.DEV && detail && (
        <pre className="mt-2 max-h-48 w-full overflow-auto rounded-xl bg-slate-100 p-3 text-left text-xs text-slate-500">{detail}</pre>
      )}
    </ErrorScene>
  )
}

/**
 * `errorElement` de la raíz del router: cualquier error al dibujar una pantalla cae aquí (a pantalla
 * completa) en lugar de dejarla en blanco.
 * - 404 lanzado por una ruta → «no encontrada»; sin red → «sin conexión»; lo demás → 500.
 */
export function RouteErrorPage() {
  const error = useRouteError()
  if (isRouteErrorResponse(error) && error.status === 404) return <NotFoundPage />
  if (!navigator.onLine) return <OfflineScreen />
  return <ServerErrorPage detail={error instanceof Error ? (error.stack ?? error.message) : String(error)} />
}
