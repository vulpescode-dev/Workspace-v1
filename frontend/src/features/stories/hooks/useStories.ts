import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { isImage, toWebp } from '@/lib/media/to-webp'

import { storiesApi, storiesKeys } from '../api/stories.api'

/** Fila de estados de Inicio. Se refresca cada 2 minutos (los estados vencen solos a las 24 h). */
export function useStoryTray() {
  return useQuery({ queryKey: storiesKeys.tray(), queryFn: storiesApi.tray, refetchInterval: 120_000 })
}

/** Subir un estado: las fotos se reducen (máx. 1920 px) y pasan a WebP antes de enviarse. */
export function useUploadStory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => storiesApi.upload(isImage(file) ? await toWebp(file, { maxSide: 1920, quality: 0.85 }) : file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: storiesKeys.tray() }),
  })
}
