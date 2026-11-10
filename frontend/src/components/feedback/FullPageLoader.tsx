import { Spinner } from '@/components/ui/Spinner'

/** Mientras se recupera la sesión al abrir la app. */
export function FullPageLoader() {
  return (
    <div className="grid min-h-dvh place-items-center text-brand-500">
      <Spinner className="size-7" label="Cargando la aplicación" />
    </div>
  )
}
