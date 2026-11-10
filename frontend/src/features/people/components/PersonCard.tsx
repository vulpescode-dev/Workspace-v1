import { Mail, UserRound } from 'lucide-react'
import type { CSSProperties } from 'react'
import { Link } from 'react-router'

import { Skeleton } from '@/components/feedback/Skeleton'
import { Card } from '@/components/ui/Card'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { FollowButton } from '@/features/follows/components/FollowButton'

import type { DirectoryPerson } from '../api/people.api'

/**
 * Color por área, calculado (nadie lo elige): cada área gira el círculo de color 137.5° (ángulo dorado)
 * por cada id, así que ninguna repite tono y las de ids cercanos quedan bien separadas. Siempre pastel
 * (mucha luz, saturación moderada) para acompañar al azul y amarillo de la marca. Sin área: azul de marca.
 */
const BRAND_HUE = 210
const GOLDEN_ANGLE = 137.508

function departmentTone(departmentId: number | null) {
  const hue = departmentId ? Math.round((BRAND_HUE + departmentId * GOLDEN_ANGLE) % 360) : BRAND_HUE
  return {
    band: `linear-gradient(135deg, hsl(${hue} 85% 90%), hsl(${(hue + 25) % 360} 80% 97%))`,
    wave: `hsl(${hue} 75% 84% / 0.6)`,
    ring: `hsl(${hue} 70% 82%)`,
    dot: `hsl(${hue} 65% 50%)`,
  }
}

const iconButton =
  'pressable grid size-9 shrink-0 place-items-center rounded-xl bg-slate-100 text-slate-500 transition-colors duration-150 hover:bg-brand-50 hover:text-brand-600'

/**
 * Tarjeta del directorio: banda con ola en el color del área › foto con doble aro › nombre › cargo ›
 * área › correo, perfil y Seguir. Todas miden lo mismo de alto (las acciones se pegan abajo) aunque
 * falte el cargo o el área. Foto y nombre llevan al perfil.
 */
export function PersonCard({ person }: { person: DirectoryPerson }) {
  const tone = departmentTone(person.department_id)
  const profileUrl = person.is_me ? '/profile' : `/profile/${person.id}`
  return (
    <Card className="group relative flex h-full flex-col overflow-hidden text-center transition-[translate,box-shadow] duration-200 ease-out hover:-translate-y-0.5 hover:shadow-md hover:shadow-slate-900/5">
      {/* Banda superior con una ola suave (adorno). */}
      <div aria-hidden className="relative h-24" style={{ backgroundImage: tone.band }}>
        <svg viewBox="0 0 400 96" preserveAspectRatio="none" className="absolute inset-0 size-full" style={{ color: tone.wave }}>
          <path fill="currentColor" d="M0 64 C 70 30, 130 92, 210 62 S 340 20, 400 46 V 0 H 0 Z" />
          <circle cx="352" cy="22" r="34" fill="currentColor" opacity="0.6" />
        </svg>
        {person.is_me && (
          <span className="absolute top-3 left-3 rounded-full bg-surface/90 px-2.5 py-0.5 text-xs font-semibold text-brand-700 shadow-sm">Tú</span>
        )}
      </div>

      <div className="flex flex-1 flex-col items-center px-5 pb-5">
        {/* `relative`: sin esto la banda (también posicionada) se pinta encima y corta el aro. */}
        <Link
          to={profileUrl}
          aria-label={`Ver perfil de ${person.name}`}
          className="relative -mt-12 grid size-[6.5rem] place-items-center rounded-full bg-surface ring-4 transition-transform duration-200 ease-out group-hover:scale-[1.03]"
          style={{ '--tw-ring-color': tone.ring } as CSSProperties}
        >
          <UserAvatar user={person} size="xl" className="!size-24 !text-2xl" />
        </Link>

        <Link to={profileUrl} className="mt-3 w-full min-w-0">
          <span className="block truncate font-display text-lg font-bold text-slate-900 hover:underline">{person.name}</span>
        </Link>
        <span className="mt-0.5 line-clamp-2 w-full text-sm font-semibold text-balance text-brand-600">{person.job_title || ' '}</span>

        {person.department ? (
          <Link
            to={`/people?department=${person.department_id}`}
            className="mt-3 inline-flex max-w-full items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 transition-colors duration-150 hover:bg-slate-200"
          >
            <span aria-hidden className="size-1.5 shrink-0 rounded-full" style={{ backgroundColor: tone.dot }} />
            <span className="truncate">{person.department}</span>
          </Link>
        ) : (
          <span className="mt-3 h-6" aria-hidden />
        )}

        <div className="mt-auto w-full pt-5">
          <div className="flex w-full items-center gap-2 border-t border-slate-100 pt-4">
            {person.email && (
              <a href={`mailto:${person.email}`} className={iconButton} aria-label={`Escribir a ${person.name}`} title={person.email}>
                <Mail className="size-4" aria-hidden />
              </a>
            )}
            <Link to={profileUrl} className={iconButton} aria-label={`Ver perfil de ${person.name}`} title="Ver perfil">
              <UserRound className="size-4" aria-hidden />
            </Link>
            <div className="min-w-0 flex-1">
              {person.is_me ? (
                <Link to="/profile" className="pressable grid h-9 place-items-center rounded-xl bg-slate-100 text-sm font-semibold text-slate-700 hover:bg-slate-200">
                  Mi perfil
                </Link>
              ) : (
                <FollowButton userId={person.id} initialFollowing={person.is_following} tone="soft" block />
              )}
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

/** Misma forma que `PersonCard`. */
export function PersonCardSkeleton() {
  return (
    <Card className="flex flex-col items-center overflow-hidden">
      <Skeleton className="h-24 w-full rounded-none" />
      <Skeleton className="relative -mt-12 size-[6.5rem] rounded-full ring-4 ring-surface" />
      <div className="flex w-full flex-col items-center gap-2 px-5 pt-3 pb-5">
        <Skeleton className="h-5 w-36" />
        <Skeleton className="h-4 w-24" />
        <Skeleton className="mt-1 h-6 w-28 rounded-full" />
        <div className="mt-3 flex w-full gap-2 border-t border-slate-100 pt-4">
          <Skeleton className="size-9 rounded-xl" />
          <Skeleton className="size-9 rounded-xl" />
          <Skeleton className="h-9 flex-1 rounded-xl" />
        </div>
      </div>
    </Card>
  )
}
