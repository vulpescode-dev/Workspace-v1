import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { accountsKeys } from '@/features/accounts/api/query-keys'
import type { Profile } from '@/features/accounts/types'
import { toWebp } from '@/lib/media/to-webp'
import type { Paginated } from '@/types/api'

import { profileApi, profileKeys } from '../api/profile.api'

/** Perfil de una persona (o el mío sin `userId`). */
export function useProfile(userId?: number) {
  return useQuery({ queryKey: profileKeys.detail(userId ?? 'me'), queryFn: () => profileApi.get(userId) })
}

/** Lista paginada («Ver más») de seguidores, seguidos o fotos. */
export function usePagedList<T>(queryKey: readonly unknown[], fetchPage: (page: number) => Promise<Paginated<T>>, enabled = true) {
  return useInfiniteQuery({
    queryKey,
    queryFn: ({ pageParam }) => fetchPage(pageParam),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page < last.total_pages ? last.page + 1 : undefined),
    enabled,
  })
}

/** Cambiar mi presentación o mi foto. Al terminar se actualiza mi perfil en toda la app (encabezado, composer…). */
export function useEditMyProfile() {
  const queryClient = useQueryClient()
  const save = (profile: Profile) => {
    queryClient.setQueryData(profileKeys.detail('me'), profile)
    queryClient.setQueryData(profileKeys.detail(profile.id), profile)
    queryClient.setQueryData(accountsKeys.me(), profile)
  }
  return {
    bio: useMutation({ mutationFn: profileApi.updateBio, onSuccess: save }),
    // Foto de perfil: cuadrada basta con 512 px.
    avatar: useMutation({ mutationFn: async (file: File) => profileApi.uploadAvatar(await toWebp(file, { maxSide: 512, quality: 0.85 })), onSuccess: save }),
    removeAvatar: useMutation({ mutationFn: profileApi.removeAvatar, onSuccess: save }),
  }
}
