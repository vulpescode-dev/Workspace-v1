import { useEffect, useRef, type ReactNode } from 'react'
import { toast } from 'sonner'

import { useOnlineStatus } from '@/hooks/useOnlineStatus'

import { preloadOfflineEmojis } from './error-emojis'
import { OfflineScreen } from './OfflineScreen'

/**
 * Envuelve toda la app (raíz del router). Sin red, muestra «Sin conexión» a pantalla completa. El contenido NO se desmonta (solo se oculta):
 * así un formulario o un borrador a medias sigue ahí cuando vuelve la conexión.
 */
export function OfflineGate({ children }: { children: ReactNode }) {
  const online = useOnlineStatus()
  const wasOffline = useRef(false)

  useEffect(() => {
    const idle = window.requestIdleCallback ?? ((callback: () => void) => window.setTimeout(callback, 1500))
    idle(() => preloadOfflineEmojis())
  }, [])

  useEffect(() => {
    if (!online) wasOffline.current = true
    else if (wasOffline.current) {
      wasOffline.current = false
      toast.success('¡De vuelta en línea!')
    }
  }, [online])

  return (
    <>
      {!online && <OfflineScreen />}
      <div className={online ? 'contents' : 'hidden'}>{children}</div>
    </>
  )
}
