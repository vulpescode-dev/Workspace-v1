import { env } from '@/config/env'
import { Logo } from '@/components/ui/Logo'
import { GoogleButton } from '@/features/auth/components/GoogleButton'
import { LoginForm } from '@/features/auth/components/LoginForm'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'

/** /login — página delgada: solo compone piezas de la feature `auth`. */
export function LoginPage() {
  useDocumentTitle('Iniciar sesión')
  return (
    <div className="grid gap-8">
      <Logo className="lg:hidden" />
      <div className="grid gap-1.5">
        <h1 className="text-2xl font-bold text-slate-900">Inicia sesión</h1>
        <p className="text-sm text-slate-500">Entra con tu cuenta de {env.projectName}.</p>
      </div>
      <LoginForm />
      <div className="flex items-center gap-3 text-xs text-slate-400">
        <span className="h-px flex-1 bg-slate-200" />o<span className="h-px flex-1 bg-slate-200" />
      </div>
      <GoogleButton />
      <p className="text-center text-xs text-slate-400">¿Olvidaste tu contraseña? Contacta a Soporte TI.</p>
    </div>
  )
}
