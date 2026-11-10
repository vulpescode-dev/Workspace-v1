import { useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/Button'

import { ERROR_EMOJIS } from './error-emojis'
import { ErrorScene } from './ErrorScene'

/**
 * Sin conexión. Se muestra en lugar del contenido mientras el navegador no tenga red y desaparece sola
 * al volver (ver `OfflineGate`). Sus emojis se precargan al abrir la app para que se vean sin red.
 */
export function OfflineScreen() {
  const [checking, setChecking] = useState(false)

  function retry() {
    setChecking(true)
    // Breve pausa: da tiempo a que el sistema reporte la red y el botón no parpadea.
    window.setTimeout(() => {
      setChecking(false)
      if (navigator.onLine) window.location.reload()
      else toast('Sigues sin conexión. Revisa tu Wi-Fi o tus datos.')
    }, 600)
  }

  return (
    <ErrorScene
      emoji={ERROR_EMOJIS.sloth}
      companions={[ERROR_EMOJIS.sleep]}
      code="Sin conexión"
      title="Tu internet se tomó una siesta"
      description="No hay conexión en este momento. En cuanto vuelva, la página se recupera sola y nada de lo que estabas escribiendo se pierde."
      actions={<Button onClick={retry} loading={checking}>Reintentar</Button>}
    />
  )
}
