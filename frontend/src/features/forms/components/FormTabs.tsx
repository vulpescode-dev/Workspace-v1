import { BarChart3, Eye, PencilLine } from 'lucide-react'
import { NavLink } from 'react-router'

import { cn } from '@/lib/cn'

/** Pestañas de quien creó el formulario: Preguntas (editor) · Respuestas · Vista previa. */
export function FormTabs({ uuid, count, edit = true, results = true }: { uuid: string; count?: number | null; edit?: boolean; results?: boolean }) {
  // `edit` / `results`: quien no es el dueño solo ve las pestañas que sus permisos le abren.
  const tabs = [
    ...(edit ? [{ to: `/forms/${uuid}/edit`, label: 'Preguntas', icon: PencilLine }] : []),
    ...(results ? [{ to: `/forms/${uuid}/results`, label: count ? `Respuestas · ${count}` : 'Respuestas', icon: BarChart3 }] : []),
    { to: `/forms/${uuid}`, label: 'Vista previa', icon: Eye },
  ]
  return (
    <nav aria-label="Secciones del formulario" className="flex gap-1 overflow-x-auto rounded-2xl bg-slate-100 p-1 [scrollbar-width:none]">
      {tabs.map(({ to, label, icon: Icon }) => (
        <NavLink key={to} to={to} end replace
          className={({ isActive }) => cn('flex h-10 shrink-0 flex-1 items-center justify-center gap-2 rounded-xl px-3 text-sm font-semibold whitespace-nowrap transition-colors duration-150', isActive ? 'bg-surface text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800')}>
          <Icon className="size-4" aria-hidden /> {label}
        </NavLink>
      ))}
    </nav>
  )
}
