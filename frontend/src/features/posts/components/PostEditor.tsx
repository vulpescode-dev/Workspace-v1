import { useState, type FormEvent } from 'react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/Button'
import { getErrorMessage } from '@/lib/api/errors'

import { useEditPost } from '../hooks/usePostMutations'
import type { Audience, Post } from '../types'
import { AudienceToggle } from './AudienceToggle'

/**
 * Edición en la misma tarjeta: texto y audiencia (las fotos y videos no se cambian aquí). Si tiene
 * fotos/videos puede quedar sin texto. Escape cancela; Ctrl/⌘ + Enter guarda.
 */
export function PostEditor({ post, onDone }: { post: Post; onDone: () => void }) {
  const edit = useEditPost()
  const [body, setBody] = useState(post.body)
  const [audience, setAudience] = useState<Audience>(post.audience)
  const empty = !body.trim() && post.attachments.length === 0
  const unchanged = body.trim() === post.body && audience === post.audience

  async function save(event?: FormEvent) {
    event?.preventDefault()
    if (empty) return
    if (unchanged) return onDone()
    try {
      await edit.mutateAsync({ postId: post.id, body: body.trim(), audience })
      toast.success('Publicación actualizada.')
      onDone()
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo guardar el cambio.'))
    }
  }

  return (
    <form onSubmit={save} className="grid gap-3 px-4 pt-3">
      <textarea
        autoFocus
        value={body}
        onChange={(event) => setBody(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Escape') onDone()
          if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) void save()
        }}
        rows={4}
        maxLength={5000}
        aria-label="Editar publicación"
        className="min-h-28 w-full resize-y rounded-xl border border-slate-200 px-3 py-2.5 text-base text-slate-900 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-[15px]"
      />
      {empty && <p className="text-sm text-red-600">La publicación no puede quedar vacía.</p>}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <AudienceToggle value={audience} onChange={setAudience} />
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={onDone} disabled={edit.isPending}>
            Cancelar
          </Button>
          <Button type="submit" size="sm" loading={edit.isPending} disabled={empty}>
            Guardar
          </Button>
        </div>
      </div>
    </form>
  )
}
