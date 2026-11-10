import { Avatar } from '@/components/ui/Avatar'
import { useProtectedImage } from '@/hooks/useProtectedImage'

import type { UserSummary } from '../types'

/** Avatar de una persona de la API: descarga su foto con sesión y, mientras tanto, muestra sus iniciales. */
export function UserAvatar({ user, size, className }: { user: UserSummary; size?: 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  const { src } = useProtectedImage(user.avatar_url, { cache: true })
  return <Avatar src={src} initials={user.initials} name={user.name} size={size} className={className} />
}
