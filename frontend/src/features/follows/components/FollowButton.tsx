import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/Button'
import { useCan } from '@/features/accounts/hooks/useCan'
import { getErrorMessage } from '@/lib/api/errors'

import { followsApi } from '../api/follows.api'

/**
 * Seguir / Siguiendo (inmediato, sin solicitud). Cambia al instante y se regresa si el servidor falla.
 * Reutilizable en sugerencias, directorio, perfil y listas de seguidores.
 */
interface FollowButtonProps {
  userId: number
  initialFollowing: boolean
  onChange?: (following: boolean) => void
  /** `soft`: azul suave (tarjetas del directorio); `block`: a todo el ancho. */
  tone?: 'solid' | 'soft'
  block?: boolean
}

export function FollowButton({ userId, initialFollowing, onChange, tone = 'solid', block = false }: FollowButtonProps) {
  const [following, setFollowing] = useState(initialFollowing)
  const canFollow = useCan()('social.follows.create')
  const mutation = useMutation({
    mutationFn: (next: boolean) => (next ? followsApi.follow(userId) : followsApi.unfollow(userId)),
    onMutate: (next) => setFollowing(next),
    onError: (error, next) => {
      setFollowing(!next)
      toast.error(getErrorMessage(error, 'No se pudo actualizar.'))
    },
    onSuccess: (_, next) => onChange?.(next),
  })

  if (!canFollow && !following) return null   // sin permiso solo se ofrece dejar de seguir

  return (
    <Button
      size="sm"
      variant={following ? 'outline' : tone === 'soft' ? 'soft' : 'primary'}
      aria-pressed={following}
      onClick={() => mutation.mutate(!following)}
      className={block ? 'h-9 w-full text-sm' : 'h-8 min-w-[5.25rem] shrink-0 px-2.5 text-xs'}
    >
      {following ? 'Siguiendo' : 'Seguir'}
    </Button>
  )
}
