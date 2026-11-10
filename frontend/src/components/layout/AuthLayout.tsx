import { Outlet } from 'react-router'

import { Logo } from '@/components/ui/Logo'

/** Pantallas sin sesión (login): panel de marca a la izquierda en escritorio, solo el formulario en teléfono. */
export function AuthLayout() {
  return (
    <div className="grid min-h-dvh lg:grid-cols-[1.05fr_1fr]">
      <section aria-hidden className="relative hidden overflow-hidden bg-brand-500 lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div className="pointer-events-none absolute -top-32 -right-24 size-[28rem] rounded-full bg-brand-400/40 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-40 -left-20 size-[26rem] rounded-full bg-accent-400/25 blur-3xl" />
        <Logo inverted className="relative" />
        <div className="relative grid max-w-md gap-4">
          <h2 className="text-4xl leading-tight font-extrabold text-white">Tu empresa, en tu bolsillo.</h2>
          <p className="text-lg text-brand-100">Publicaciones, avisos, documentos y personas en un solo lugar.</p>
        </div>
        <p className="relative text-sm text-brand-200">Intranet de uso interno.</p>
      </section>

      <main className="flex items-center justify-center px-4 py-10 sm:px-6">
        <div className="w-full max-w-sm animate-enter">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
