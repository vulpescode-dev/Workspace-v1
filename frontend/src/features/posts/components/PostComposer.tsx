import { ImagePlus, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { useMe } from '@/features/accounts/hooks/useMe'
import { getErrorMessage } from '@/lib/api/errors'
import { cn } from '@/lib/cn'
import { isImage, isVideo, toWebp } from '@/lib/media/to-webp'

import { useCreatePost } from '../hooks/usePostMutations'
import type { Audience } from '../types'
import { AudienceToggle } from './AudienceToggle'

const MAX_FILES = 10
const MAX_CHARS = 5000

/**
 * «¿Qué quieres compartir?». Cerrado es una sola línea; al tocarlo se abre el editor con texto,
 * audiencia y fotos/videos. Las fotos se convierten a WebP en el navegador justo antes de publicar.
 */
export function PostComposer() {
  const { data: me } = useMe()
  const create = useCreatePost()
  const [open, setOpen] = useState(false)
  const [body, setBody] = useState('')
  const [audience, setAudience] = useState<Audience>('company')
  const [files, setFiles] = useState<File[]>([])
  const [preparing, setPreparing] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const firstName = me?.first_name.split(' ')[0]
  const busy = preparing || create.isPending
  const canPublish = (body.trim().length > 0 || files.length > 0) && !busy

  function reset() {
    setOpen(false)
    setBody('')
    setAudience('company')
    setFiles([])
  }

  function addFiles(list: FileList | null) {
    const picked = Array.from(list ?? []).filter((file) => isImage(file) || isVideo(file))
    if (files.length + picked.length > MAX_FILES) toast.error(`Máximo ${MAX_FILES} fotos o videos por publicación.`)
    setFiles((current) => [...current, ...picked].slice(0, MAX_FILES))
    setOpen(true)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!canPublish) return
    try {
      setPreparing(true)
      const ready = await Promise.all(files.map((file) => (isImage(file) ? toWebp(file) : file)))
      setPreparing(false)
      await create.mutateAsync({ body: body.trim(), audience, files: ready })
      toast.success('Publicado.')
      reset()
    } catch (error) {
      setPreparing(false)
      toast.error(error instanceof Error && !('isAxiosError' in error) ? error.message : getErrorMessage(error, 'No se pudo publicar.'))
    }
  }

  return (
    <Card className="p-4">
      <form onSubmit={handleSubmit}>
        <div className="flex items-start gap-3">
          {me ? <UserAvatar user={me} /> : <span className="size-10 shrink-0 rounded-full bg-slate-200" />}
          {open ? (
            <textarea
              autoFocus
              value={body}
              onChange={(event) => setBody(event.target.value)}
              maxLength={MAX_CHARS}
              rows={3}
              placeholder={`¿Qué quieres compartir${firstName ? `, ${firstName}` : ''}?`}
              aria-label="Texto de la publicación"
              className="min-h-24 w-full resize-y rounded-xl border border-slate-200 px-3 py-2.5 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-[15px]"
            />
          ) : (
            <button
              type="button"
              onClick={() => setOpen(true)}
              className="flex h-10 flex-1 items-center rounded-full bg-slate-100 px-4 text-left text-sm text-slate-500 transition-colors duration-150 hover:bg-slate-200/70"
            >
              ¿Qué quieres compartir{firstName ? `, ${firstName}` : ''}?
            </button>
          )}
          {!open && (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              aria-label="Agregar fotos o videos"
              className="pressable grid size-10 shrink-0 place-items-center rounded-full text-emerald-600 transition-colors duration-150 hover:bg-emerald-50"
            >
              <ImagePlus className="size-5" aria-hidden />
            </button>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,video/mp4,video/quicktime,video/webm"
          multiple
          hidden
          onChange={(event) => {
            addFiles(event.target.files)
            event.target.value = ''
          }}
        />

        {open && (
          <div className="mt-3 grid gap-3 animate-enter">
            {files.length > 0 && <FilePreviews files={files} onRemove={(index) => setFiles((current) => current.filter((_, i) => i !== index))} />}

            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-3">
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={files.length >= MAX_FILES || busy}
                  className="pressable flex h-9 items-center gap-2 rounded-xl px-3 text-sm font-semibold text-slate-600 transition-colors duration-150 hover:bg-slate-100 disabled:opacity-50"
                >
                  <ImagePlus className="size-5 text-emerald-600" aria-hidden />
                  Foto/video
                </button>
                <AudienceToggle value={audience} onChange={setAudience} />
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={reset} disabled={busy}>
                  Cancelar
                </Button>
                <Button type="submit" size="sm" loading={busy} disabled={!canPublish}>
                  Publicar
                </Button>
              </div>
            </div>
          </div>
        )}
      </form>
    </Card>
  )
}

function FilePreviews({ files, onRemove }: { files: File[]; onRemove: (index: number) => void }) {
  const urls = useMemo(() => files.map((file) => (isImage(file) ? URL.createObjectURL(file) : null)), [files])
  useEffect(() => () => urls.forEach((url) => url && URL.revokeObjectURL(url)), [urls])

  return (
    <ul className="grid grid-cols-4 gap-2 sm:grid-cols-5">
      {files.map((file, index) => (
        <li key={`${file.name}-${index}`} className="relative aspect-square overflow-hidden rounded-xl bg-slate-100">
          {urls[index] ? (
            <img src={urls[index]!} alt={file.name} className="size-full object-cover" />
          ) : (
            <span className="grid size-full place-items-center px-1 text-center text-[11px] font-medium text-slate-500">Video</span>
          )}
          <button
            type="button"
            onClick={() => onRemove(index)}
            aria-label={`Quitar ${file.name}`}
            className={cn('pressable absolute top-1 right-1 grid size-6 place-items-center rounded-full bg-slate-950/60 text-white')}
          >
            <X className="size-3.5" aria-hidden />
          </button>
        </li>
      ))}
    </ul>
  )
}
