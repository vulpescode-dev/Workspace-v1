import { Plus } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { Skeleton, SkeletonGroup } from '@/components/feedback/Skeleton'
import { Spinner } from '@/components/ui/Spinner'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { useCan } from '@/features/accounts/hooks/useCan'
import { useMe } from '@/features/accounts/hooks/useMe'
import { getErrorMessage } from '@/lib/api/errors'

import { useStoryTray, useUploadStory } from '../hooks/useStories'
import type { StoryGroup } from '../types'
import { StoryRing } from './StoryRing'
import { StoryViewer } from './StoryViewer'

/**
 * Fila de estados en Inicio (como Instagram): solo la foto de cada persona con su aro, no tarjetas con
 * el contenido (más ligero: no se descarga ninguna foto/video hasta abrir uno).
 * - Primero «Tu estado»: el «+» sube una foto o un video (dura 24 horas). Con estados vivos lleva aro de
 *   color y tocar la foto los abre; sin estados, tocar la foto también sube uno.
 * - Luego quien tiene estados sin ver (aro de color) y al final los ya vistos (aro gris). Tocar abre el visor.
 */
export function StoryTray() {
  const { data: me } = useMe()
  const canUpload = useCan()('social.stories.create')
  const tray = useStoryTray()
  const upload = useUploadStory()
  const inputRef = useRef<HTMLInputElement>(null)
  // Se abre con una copia de la fila: si se actualiza mientras ves estados, el orden no cambia bajo tus dedos.
  const [viewer, setViewer] = useState<{ groups: StoryGroup[]; start: number } | null>(null)

  if (tray.isPending) return <StoryTraySkeleton />
  if (tray.isError) return null   // los estados son un extra: si fallan, el feed sigue

  const mine = tray.data.find((group) => group.is_mine)
  const others = tray.data.filter((group) => !group.is_mine)
  const openViewer = (group: StoryGroup) => setViewer({ groups: tray.data, start: tray.data.indexOf(group) })

  function pick(file: File | undefined) {
    if (!file) return
    upload.mutate(file, {
      onSuccess: () => toast.success('Tu estado se publicó. Se verá durante 24 horas.'),
      onError: (error) => toast.error(error instanceof Error && !('isAxiosError' in error) ? error.message : getErrorMessage(error, 'No se pudo subir tu estado.')),
    })
  }

  return (
    <section aria-label="Estados" className="-mx-4 sm:mx-0">
      <ul className="flex gap-3 overflow-x-auto px-4 pb-1 [scrollbar-width:none] sm:px-0 [&::-webkit-scrollbar]:hidden">
        {/* «Tu estado»: sin permiso de subir solo aparece si ya tienes estados (para verlos). */}
        {(canUpload || mine) && (
        <li className="relative shrink-0">
          <button
            type="button"
            onClick={() => (mine ? openViewer(mine) : inputRef.current?.click())}
            disabled={upload.isPending}
            aria-label={mine ? 'Ver tu estado' : 'Subir un estado (foto o video, dura 24 horas)'}
            className="pressable flex w-[4.5rem] flex-col items-center gap-1.5"
          >
            <StoryRing state={mine ? 'unseen' : 'none'}>
              {me ? <UserAvatar user={me} size="lg" /> : <span className="size-14 rounded-full bg-slate-200" />}
            </StoryRing>
            <span className="w-full truncate text-center text-xs font-medium text-slate-700">{upload.isPending ? 'Subiendo…' : 'Tu estado'}</span>
          </button>
          {canUpload && (
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={upload.isPending}
            aria-label={mine ? 'Agregar otro estado' : 'Subir un estado'}
            className="pressable absolute top-[2.85rem] right-1 grid size-6 place-items-center rounded-full bg-brand-500 text-white ring-[3px] ring-canvas"
          >
            {upload.isPending ? <Spinner className="size-3.5" label="Subiendo estado" /> : <Plus className="size-4" strokeWidth={3} aria-hidden />}
          </button>
          )}
          <input
            ref={inputRef}
            type="file"
            accept="image/*,video/mp4,video/quicktime,video/webm"
            hidden
            onChange={(event) => {
              pick(event.target.files?.[0])
              event.target.value = ''
            }}
          />
        </li>
        )}

        {others.map((group) => (
          <li key={group.author.id} className="shrink-0">
            <StoryBubble group={group} onOpen={() => openViewer(group)} />
          </li>
        ))}

        {others.length === 0 && canUpload && (
          <li className="flex items-center pl-1 text-sm text-slate-500">Comparte una foto o un video del día: dura 24 horas.</li>
        )}
      </ul>
      {viewer && <StoryViewer groups={viewer.groups} startGroup={viewer.start} onClose={() => setViewer(null)} />}
    </section>
  )
}

function StoryBubble({ group, onOpen }: { group: StoryGroup; onOpen: () => void }) {
  const firstName = group.author.name.split(' ')[0]
  return (
    <button
      type="button"
      onClick={onOpen}
      aria-label={`Estados de ${group.author.name}${group.has_unseen ? ', sin ver' : ''}`}
      className="pressable flex w-[4.5rem] flex-col items-center gap-1.5"
    >
      <StoryRing state={group.has_unseen ? 'unseen' : 'seen'}>
        <UserAvatar user={group.author} size="lg" />
      </StoryRing>
      <span className={`w-full truncate text-center text-xs ${group.has_unseen ? 'font-semibold text-slate-900' : 'font-medium text-slate-500'}`}>
        {firstName}
      </span>
    </button>
  )
}

function StoryTraySkeleton() {
  return (
    <SkeletonGroup label="Cargando estados" className="flex gap-3 overflow-hidden">
      {Array.from({ length: 6 }, (_, index) => (
        <div key={index} className="flex w-[4.5rem] shrink-0 flex-col items-center gap-1.5">
          <Skeleton className="size-[4.125rem] rounded-full" />
          <Skeleton className="h-3 w-12" />
        </div>
      ))}
    </SkeletonGroup>
  )
}
