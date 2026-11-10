import { Link } from 'react-router'

import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import type { Person } from '@/features/accounts/types'

import { FollowButton } from './FollowButton'

/**
 * Una persona en una lista (sugerencias, seguidores, seguidos): foto y nombre enlazan a su perfil,
 * cargo debajo y botón Seguir (no en mi propia fila). Nombres largos se cortan con «…».
 */
export function PersonRow({ person }: { person: Person }) {
  return (
    <li className="flex items-center gap-3">
      <Link to={`/profile/${person.id}`} className="flex min-w-0 flex-1 items-center gap-3 rounded-xl">
        <UserAvatar user={person} />
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-semibold text-slate-900 hover:underline">{person.name}</span>
          {person.job_title && <span className="block truncate text-xs text-slate-500">{person.job_title}</span>}
        </span>
      </Link>
      {!person.is_me && <FollowButton userId={person.id} initialFollowing={person.is_following} />}
    </li>
  )
}
