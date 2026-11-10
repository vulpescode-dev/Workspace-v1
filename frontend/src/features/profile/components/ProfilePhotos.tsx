import { Images } from 'lucide-react'
import { useState } from 'react'

import { EmptyState } from '@/components/feedback/EmptyState'
import { Skeleton } from '@/components/feedback/Skeleton'
import { ProtectedImage } from '@/components/media/ProtectedImage'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { PostGallery } from '@/features/posts/components/PostGallery'
import type { PostAttachment } from '@/features/posts/types'
import { cn } from '@/lib/cn'

import { profileApi, profileKeys } from '../api/profile.api'
import { usePagedList } from '../hooks/useProfile'

interface ProfilePhotosProps {
  userId: number
  /** Pestaña Todo: solo 9 en 3×3 y «Ver todas». */
  preview?: boolean
  onShowAll?: () => void
}

/** Fotos de las publicaciones de la persona (lo más nuevo primero). Tocar una abre la galería. */
export function ProfilePhotos({ userId, preview = false, onShowAll }: ProfilePhotosProps) {
  const list = usePagedList(profileKeys.photos(userId), (page) => profileApi.photos(userId, page))
  const [galleryAt, setGalleryAt] = useState<number | null>(null)
  const photos = list.data?.pages.flatMap((page) => page.results) ?? []
  const shown = preview ? photos.slice(0, 9) : photos
  const asAttachments: PostAttachment[] = photos.map((photo) => ({
    id: photo.id, kind: 'image', url: photo.url, content_type: 'image/webp', size: 0, width: photo.width, height: photo.height,
  }))

  return (
    <Card className="p-5">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-bold text-slate-900">Fotos</h2>
        {preview && photos.length > 0 && (
          <button type="button" onClick={onShowAll} className="text-sm font-semibold text-brand-600 hover:text-brand-700">
            Ver todas
          </button>
        )}
      </div>

      {list.isPending ? (
        <div className={cn('grid grid-cols-3 gap-1', !preview && 'sm:grid-cols-4 lg:grid-cols-5')} aria-hidden>
          {Array.from({ length: preview ? 6 : 10 }, (_, index) => <Skeleton key={index} className="aspect-square rounded-lg" />)}
        </div>
      ) : list.isError ? (
        <p className="text-sm text-slate-500">No se pudieron cargar las fotos.</p>
      ) : photos.length === 0 ? (
        <EmptyState icon={Images} title="Sin fotos todavía" description="Las fotos de sus publicaciones aparecerán aquí." />
      ) : (
        <ul className={cn('grid grid-cols-3 gap-1', !preview && 'sm:grid-cols-4 lg:grid-cols-5')}>
          {shown.map((photo, index) => (
            <li key={photo.id}>
              <button type="button" onClick={() => setGalleryAt(index)} aria-label={`Ver foto ${index + 1}`} className="block aspect-square w-full overflow-hidden rounded-lg">
                <ProtectedImage url={photo.url} alt="Foto de una publicación" className="size-full" />
              </button>
            </li>
          ))}
        </ul>
      )}

      {!preview && list.hasNextPage && (
        <Button variant="ghost" size="sm" className="mt-3 w-full" loading={list.isFetchingNextPage} onClick={() => void list.fetchNextPage()}>
          Ver más fotos
        </Button>
      )}
      {galleryAt !== null && <PostGallery attachments={asAttachments} startIndex={galleryAt} onClose={() => setGalleryAt(null)} />}
    </Card>
  )
}
