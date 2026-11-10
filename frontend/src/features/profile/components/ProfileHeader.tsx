import { useQueryClient } from '@tanstack/react-query'
import { Cake, Mail, Pencil } from 'lucide-react'

import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import type { Profile } from '@/features/accounts/types'
import { FollowButton } from '@/features/follows/components/FollowButton'

import { profileKeys } from '../api/profile.api'
import { formatBirthday } from '../utils/format'

interface ProfileHeaderProps {
  profile: Profile
  onEdit: () => void
  onShowPeople: () => void
}

/**
 * Encabezado del perfil. Teléfono: portada, foto centrada encima y datos debajo. Escritorio (≥ 1024 px):
 * portada ancha, foto a la izquierda, nombre · cargo · área · cumpleaños y acciones a la derecha.
 * La portada es el degradado de la marca (la imagen definitiva está pendiente).
 */
export function ProfileHeader({ profile, onEdit, onShowPeople }: ProfileHeaderProps) {
  const queryClient = useQueryClient()
  const subtitle = [profile.job_title, profile.department].filter(Boolean).join(' · ')

  return (
    <Card className="overflow-hidden">
      <div aria-hidden className="h-32 bg-[linear-gradient(120deg,var(--color-brand-700),var(--color-brand-500)_55%,var(--color-accent-400))] sm:h-48" />
      <div className="px-4 pb-5 sm:px-8">
        <div className="flex flex-col items-center gap-4 lg:flex-row lg:items-end">
          <span className="-mt-14 inline-grid rounded-full bg-surface p-1 shadow-sm sm:-mt-20">
            <UserAvatar user={profile} size="xl" />
          </span>
          <div className="min-w-0 flex-1 text-center lg:pb-2 lg:text-left">
            <h1 className="text-2xl font-extrabold text-slate-900 sm:text-3xl">{profile.name}</h1>
            {subtitle && <p className="mt-1 text-sm text-slate-600 sm:text-base">{subtitle}</p>}
            <div className="mt-2 flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-sm text-slate-500 lg:justify-start">
              <span>
                <strong className="font-semibold text-slate-900 tabular-nums">{profile.posts_count}</strong> publicaciones
              </span>
              <button type="button" onClick={onShowPeople} className="hover:text-slate-800">
                <strong className="font-semibold text-slate-900 tabular-nums">{profile.follow.followers_count}</strong> seguidores
              </button>
              <button type="button" onClick={onShowPeople} className="hover:text-slate-800">
                <strong className="font-semibold text-slate-900 tabular-nums">{profile.follow.following_count}</strong> seguidos
              </button>
              {profile.birthday && (
                <span className="inline-flex items-center gap-1.5">
                  <Cake className="size-4" aria-hidden /> {formatBirthday(profile.birthday)}
                </span>
              )}
            </div>
          </div>
          <div className="flex shrink-0 flex-wrap items-center justify-center gap-2 lg:pb-2">
            {profile.is_me ? (
              <Button variant="outline" onClick={onEdit}>
                <Pencil className="size-4" aria-hidden /> Editar perfil
              </Button>
            ) : (
              <>
                {profile.follow.follows_me && <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">Te sigue</span>}
                <FollowButton
                  userId={profile.id}
                  initialFollowing={profile.follow.is_following}
                  onChange={() => void queryClient.invalidateQueries({ queryKey: profileKeys.detail(profile.id) })}
                />
                {profile.email && (
                  <a
                    href={`mailto:${profile.email}`}
                    className="pressable inline-flex h-8 items-center gap-2 rounded-xl border border-slate-200 px-3 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    <Mail className="size-4" aria-hidden /> Enviar correo
                  </a>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </Card>
  )
}
