import { useState, type ButtonHTMLAttributes } from 'react'

import { Link } from 'react-router'

import { Avatar } from '@/components/ui/Avatar'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { ReactionPicker } from '@/features/reactions/components/ReactionPicker'
import { ReactionSummaryChips } from '@/features/reactions/components/ReactionSummaryChips'
import { cn } from '@/lib/cn'
import { formatFullDateTime, formatRelative } from '@/lib/format'

import type { Comment } from '../types'

interface CommentItemProps {
  comment: Comment
  isReply?: boolean
  /** Sin permiso para comentar no se pasa y no aparece «Responder». */
  onReply?: () => void
  /** Sin permiso (`*.comments.update`) no se pasa y no aparece «Editar» (solo en los propios). */
  onEdit?: (body: string) => Promise<unknown>
  /** Propio con `*.comments.delete`, o ajeno con `*.comments.delete.all` (moderación). Sin él, no aparece «Eliminar». */
  onDelete?: () => void
  /** Sin `onReact` (blog) no se muestran reacciones. */
  onReact?: (emoji: string | null) => void
}

/** Un comentario: foto, burbuja (nombre + texto), y debajo: tiempo · Responder · Reaccionar · Editar/Eliminar. */
export function CommentItem({ comment, isReply = false, onReply, onEdit, onDelete, onReact }: CommentItemProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(comment.body)
  const [saving, setSaving] = useState(false)
  const [celebrate, setCelebrate] = useState<{ code: string; key: number } | null>(null)

  if (comment.is_deleted || !comment.author) {
    return (
      <div className="flex items-center gap-2.5">
        <Avatar initials="" name="Comentario eliminado" size={isReply ? 'sm' : 'md'} className="bg-slate-100" />
        <p className="rounded-2xl bg-slate-50 px-3 py-2 text-sm text-slate-400 italic">Comentario eliminado</p>
      </div>
    )
  }

  const reactions = onReact ? comment.reactions : undefined
  function react(code: string | null) {
    onReact?.(code)
    if (code) setCelebrate({ code, key: Date.now() })
  }

  async function save() {
    const body = draft.trim()
    if (!body || body === comment.body) return setEditing(false)
    setSaving(true)
    try {
      await onEdit?.(body)
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex gap-2.5">
      <UserAvatar user={comment.author} size={isReply ? 'sm' : 'md'} />
      <div className="min-w-0 flex-1">
        <div className="inline-block max-w-full rounded-2xl bg-slate-100 px-3 py-2">
          <Link to={`/profile/${comment.author.id}`} className="text-[13px] font-semibold text-slate-900 hover:underline">
            {comment.author.name}
          </Link>
          {editing ? (
            <textarea
              autoFocus
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Escape') setEditing(false)
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  void save()
                }
              }}
              rows={2}
              aria-label="Editar comentario"
              className="mt-1 w-72 max-w-full resize-y rounded-lg border border-slate-200 bg-surface px-2 py-1.5 text-base sm:text-sm"
            />
          ) : (
            <p className="text-sm break-words whitespace-pre-line text-slate-800">{comment.body}</p>
          )}
        </div>

        {reactions && reactions.total > 0 && (
          <div className="mt-1.5">
            <ReactionSummaryChips summary={reactions} onToggle={(code) => react(code === reactions.mine ? null : code)} celebrate={celebrate} />
          </div>
        )}

        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 px-1 text-xs font-semibold text-slate-500">
          <time dateTime={comment.created_at} title={formatFullDateTime(comment.created_at)} className="font-normal">
            {formatRelative(comment.created_at)}
            {comment.edited_at && ' · editado'}
          </time>
          {editing ? (
            <>
              <MetaButton onClick={() => void save()} disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</MetaButton>
              <MetaButton onClick={() => setEditing(false)}>Cancelar</MetaButton>
            </>
          ) : (
            <>
              {reactions && <ReactionPicker mine={reactions.mine} onPick={react} compact nested />}
              {onReply && <MetaButton onClick={onReply}>Responder</MetaButton>}
              {comment.is_mine && onEdit && <MetaButton onClick={() => { setDraft(comment.body); setEditing(true) }}>Editar</MetaButton>}
              {onDelete && <MetaButton onClick={onDelete} className="hover:text-red-600">Eliminar</MetaButton>}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function MetaButton({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button type="button" className={cn('rounded py-0.5 hover:text-slate-800 disabled:opacity-60', className)} {...props} />
}
