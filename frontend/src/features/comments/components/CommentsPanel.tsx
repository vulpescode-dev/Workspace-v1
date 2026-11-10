import { MessageCircle, SendHorizontal, X } from 'lucide-react'
import { useRef, useState, type FormEvent } from 'react'

import { EmptyState } from '@/components/feedback/EmptyState'
import { ListSkeleton } from '@/components/feedback/ListSkeleton'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { useCan } from '@/features/accounts/hooks/useCan'
import { useMe } from '@/features/accounts/hooks/useMe'
import { cn } from '@/lib/cn'

import type { CommentSource } from '../api/comments.api'
import { useCommentMutations, useComments } from '../hooks/useComments'
import type { Comment } from '../types'
import { CommentItem } from './CommentItem'

interface CommentsPanelProps {
  source: CommentSource
  /** Pedir los comentarios (la hoja solo los pide al abrirse). */
  enabled?: boolean
  onCountChange: (count: number) => void
  /** Dentro de una hoja: la lista hace scroll y la caja queda fija abajo. En línea (blog): fluye con la página. */
  inSheet?: boolean
}

/** Hilos con respuestas de un nivel y la caja para escribir. Lo usan la hoja de comentarios y el blog. */
export function CommentsPanel({ source, enabled = true, onCountChange, inSheet = false }: CommentsPanelProps) {
  const { data: me } = useMe()
  const can = useCan()
  const canComment = can(source.permission)
  // Mismo recurso que el permiso de comentar: «social.comments» o «blog.comments».
  const resource = source.permission.replace(/\.create$/, '')
  const canEdit = can(`${resource}.update`)
  const canDelete = (comment: Comment) => can(comment.is_mine ? `${resource}.delete` : `${resource}.delete.all`)
  const threads = useComments(source, enabled)
  const { create, edit, remove, react } = useCommentMutations(source, onCountChange)
  const [body, setBody] = useState('')
  const [replyTo, setReplyTo] = useState<{ id: number; name: string } | null>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Responder a una respuesta cuelga del mismo hilo (un solo nivel).
  function startReply(threadId: number, comment: Comment) {
    setReplyTo({ id: threadId, name: comment.author?.name ?? 'comentario' })
    inputRef.current?.focus()
  }

  async function submit(event?: FormEvent) {
    event?.preventDefault()
    const text = body.trim()
    if (!text || create.isPending) return
    await create.mutateAsync({ body: text, parent: replyTo?.id ?? null })
    setBody('')
    setReplyTo(null)
  }

  function confirmDelete(comment: Comment) {
    if (window.confirm('¿Eliminar este comentario?')) remove.mutate(comment.id)
  }

  const items = threads.data?.pages.flatMap((page) => page.results) ?? []

  return (
    <>
      <div className={cn('px-4 py-4', inSheet && 'flex-1 overflow-y-auto overscroll-contain')}>
        {threads.isPending ? (
          <ListSkeleton rows={4} label="Cargando comentarios" />
        ) : threads.isError ? (
          <EmptyState
            icon={MessageCircle}
            title="No se pudieron cargar los comentarios"
            action={<Button variant="outline" size="sm" onClick={() => void threads.refetch()}>Reintentar</Button>}
          />
        ) : items.length === 0 ? (
          <EmptyState icon={MessageCircle} title="Aún no hay comentarios" description="Sé la primera persona en comentar." />
        ) : (
          <ul className="grid gap-4">
            {items.map((thread) => (
              <li key={thread.id} className="grid gap-3">
                <CommentItem
                  comment={thread}
                  onReply={canComment ? () => startReply(thread.id, thread) : undefined}
                  onEdit={canEdit ? (text) => edit.mutateAsync({ id: thread.id, body: text }) : undefined}
                  onDelete={canDelete(thread) ? () => confirmDelete(thread) : undefined}
                  onReact={source.react && ((emoji) => react.mutate({ id: thread.id, emoji }))}
                />
                {thread.replies.length > 0 && (
                  <ul className="ml-12 grid gap-3">
                    {thread.replies.map((reply) => (
                      <li key={reply.id}>
                        <CommentItem
                          comment={reply}
                          isReply
                          onReply={canComment ? () => startReply(thread.id, reply) : undefined}
                          onEdit={canEdit ? (text) => edit.mutateAsync({ id: reply.id, body: text }) : undefined}
                          onDelete={canDelete(reply) ? () => confirmDelete(reply) : undefined}
                          onReact={source.react && ((emoji) => react.mutate({ id: reply.id, emoji }))}
                        />
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        )}
        {threads.hasNextPage && (
          <Button variant="ghost" size="sm" className="mt-4 w-full" loading={threads.isFetchingNextPage} onClick={() => void threads.fetchNextPage()}>
            Ver más comentarios
          </Button>
        )}
      </div>

      {canComment && (
      <form onSubmit={submit} className={cn('border-t border-slate-100 px-4 pt-3', inSheet ? 'pb-[calc(0.75rem+env(safe-area-inset-bottom))]' : 'pb-4')}>
        {replyTo && (
          <p className="mb-2 flex items-center justify-between rounded-lg bg-brand-50 px-3 py-1.5 text-xs text-brand-700">
            Respondiendo a <strong className="ml-1 flex-1 truncate">{replyTo.name}</strong>
            <button type="button" onClick={() => setReplyTo(null)} aria-label="Cancelar respuesta" className="ml-2 rounded p-0.5 hover:bg-brand-100">
              <X className="size-3.5" aria-hidden />
            </button>
          </p>
        )}
        <div className="flex items-end gap-2">
          {me && <UserAvatar user={me} size="sm" />}
          <textarea
            ref={inputRef}
            value={body}
            onChange={(event) => setBody(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) void submit(event)
            }}
            rows={1}
            maxLength={2000}
            placeholder={replyTo ? 'Escribe una respuesta…' : 'Escribe un comentario…'}
            aria-label="Comentario"
            className="max-h-32 min-h-10 flex-1 resize-none rounded-2xl bg-slate-100 px-4 py-2.5 text-base text-slate-900 placeholder:text-slate-400 focus:bg-surface focus:ring-2 focus:ring-brand-500/30 focus:outline-none sm:text-sm"
          />
          <button
            type="submit"
            disabled={!body.trim() || create.isPending}
            aria-label="Enviar comentario"
            className="pressable grid size-10 shrink-0 place-items-center rounded-full bg-brand-500 text-white transition-opacity duration-150 disabled:opacity-40"
          >
            {create.isPending ? <Spinner className="size-4" label="Enviando" /> : <SendHorizontal className="size-4" aria-hidden />}
          </button>
        </div>
      </form>
      )}
    </>
  )
}
