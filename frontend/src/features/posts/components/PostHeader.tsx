import { Ellipsis, Globe, Info, Pencil, Trash2, Users } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'

import { Menu } from '@/components/ui/Menu'
import { useCan } from '@/features/accounts/hooks/useCan'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { formatFullDateTime, formatRelative } from '@/lib/format'

import { AUDIENCE_LABELS, type Post } from '../types'
import { PostInfoSheet } from './PostInfoSheet'

interface PostHeaderProps {
  post: Post
  onEdit: () => void
  onDelete: () => void
}

/**
 * Autor, cuándo se publicó (relativo; la fecha completa al pasar el mouse) y para quién. Menú «…»:
 * «Información» para todos; Editar / Eliminar según permisos (el servidor también lo valida).
 */
export function PostHeader({ post, onEdit, onDelete }: PostHeaderProps) {
  const can = useCan()
  const [showInfo, setShowInfo] = useState(false)
  // Información: para cualquiera que vea la publicación. Lo propio: editar/eliminar con su permiso. Lo ajeno: solo eliminar, con «delete.all» (moderación).
  const menu = [
    { label: 'Información', icon: Info, onSelect: () => setShowInfo(true) },
    ...(post.is_mine && can('social.posts.update') ? [{ label: 'Editar', icon: Pencil, onSelect: onEdit }] : []),
    ...(can(post.is_mine ? 'social.posts.delete' : 'social.posts.delete.all')
      ? [{ label: 'Eliminar', icon: Trash2, onSelect: onDelete, danger: true }]
      : []),
  ]
  const AudienceIcon = post.audience === 'followers' ? Users : Globe
  return (
    <header className="flex items-center gap-3 px-4 pt-4">
      <Link to={`/profile/${post.author.id}`} aria-hidden tabIndex={-1} className="shrink-0 rounded-full">
        <UserAvatar user={post.author} />
      </Link>
      <div className="min-w-0 flex-1">
        <Link id={`post-${post.id}-author`} to={`/profile/${post.author.id}`} className="block truncate text-sm font-semibold text-slate-900 hover:underline">
          {post.author.name}
        </Link>
        <p className="flex items-center gap-1.5 text-xs text-slate-500">
          <time dateTime={post.created_at} title={formatFullDateTime(post.created_at)}>
            {formatRelative(post.created_at)}
          </time>
          {post.edited_at && <span title={`Editado: ${formatFullDateTime(post.edited_at)}`}>· editado</span>}
          <span aria-hidden>·</span>
          <AudienceIcon className="size-3.5" aria-label={AUDIENCE_LABELS[post.audience]} />
        </p>
      </div>
      <Menu label="Opciones de la publicación" trigger={<Ellipsis className="size-5" aria-hidden />} items={menu} />
      {showInfo && <PostInfoSheet post={post} onClose={() => setShowInfo(false)} />}
    </header>
  )
}
