import { Briefcase, Building2, Cake, CalendarDays, Mail, UserRound } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router'

import { Card } from '@/components/ui/Card'
import { env } from '@/config/env'
import type { Profile } from '@/features/accounts/types'
import { cn } from '@/lib/cn'

import { formatBirthday, formatMonthYear } from '../utils/format'

/**
 * Datos de la persona. `compact`: tarjeta «Datos» de la pestaña Todo. Completo: pestaña Información
 * (dos columnas en escritorio). Lo vacío no se muestra (nada de «Sin dato»).
 */
export function ProfileInfo({ profile, compact = false }: { profile: Profile; compact?: boolean }) {
  const rows: { icon: typeof Mail; label: string; value: ReactNode }[] = []
  if (profile.job_title) rows.push({ icon: Briefcase, label: 'Cargo', value: profile.job_title })
  if (profile.department) {
    rows.push({
      icon: Building2,
      label: 'Área',
      value: profile.department_id ? (
        <Link to={`/people?department=${profile.department_id}`} className="text-brand-600 hover:underline">{profile.department}</Link>
      ) : profile.department,
    })
  }
  if (profile.manager) {
    rows.push({ icon: UserRound, label: 'Jefe directo', value: <Link to={`/profile/${profile.manager.id}`} className="text-brand-600 hover:underline">{profile.manager.name}</Link> })
  }
  if (profile.email) rows.push({ icon: Mail, label: 'Correo', value: <a href={`mailto:${profile.email}`} className="break-all text-brand-600 hover:underline">{profile.email}</a> })
  if (profile.birthday) rows.push({ icon: Cake, label: 'Cumpleaños', value: formatBirthday(profile.birthday) })
  rows.push({ icon: CalendarDays, label: `En ${env.projectName} desde`, value: formatMonthYear(profile.date_joined) })

  return (
    <Card className="p-5">
      <h2 className="text-base font-bold text-slate-900">{compact ? 'Datos' : 'Información'}</h2>
      {profile.bio && <p className="mt-3 text-sm whitespace-pre-line text-slate-700">{profile.bio}</p>}
      <dl className={cn('mt-4 grid grid-cols-1 gap-4', !compact && 'sm:grid-cols-2')}>
        {rows.map(({ icon: Icon, label, value }) => (
          <div key={label} className="flex min-w-0 gap-3">
            <Icon className="mt-0.5 size-5 shrink-0 text-slate-400" aria-hidden />
            <div className="min-w-0">
              <dt className="text-xs text-slate-500">{label}</dt>
              <dd className="text-sm font-medium text-slate-800">{value}</dd>
            </div>
          </div>
        ))}
      </dl>
    </Card>
  )
}
