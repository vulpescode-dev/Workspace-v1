import { CalendarClock, Globe, Hash, Image as ImageIcon, Link2, MessageCircle, PencilLine, SmilePlus, UserRound, Users, type LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { toast } from 'sonner'

import { Button } from '@/components/ui/Button'
import { Sheet } from '@/components/ui/Sheet'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { formatFullDateTime, formatRelative } from '@/lib/format'

import { AUDIENCE_LABELS, type Post } from '../types'

const AUDIENCE_HELP: Record<Post['audience'], string> = {
  company: 'La puede ver cualquier persona de la empresa.',
  followers: 'Solo la ven quienes siguen a su autor (y su autor).',
}

const plural = (count: number, one: string, many: string) => `${count} ${count === 1 ? one : many}`

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

/**
 * «Información» de una publicación (menú «…», para cualquiera que la vea): quién la publicó, cuándo, si se
 * editó, quién puede verla, qué contiene y su actividad. Todo sale de la publicación que ya se tiene: no
 * pide nada al servidor ni muestra nada que no sea visible ya.
 */
export function PostInfoSheet({ post, onClose }: { post: Post; onClose: () => void }) {
  const images = post.attachments.filter((item) => item.kind === 'image').length
  const videos = post.attachments.length - images
  const totalSize = post.attachments.reduce((sum, item) => sum + item.size, 0)
  const content = [
    post.body.trim() && plural(post.body.trim().length, 'carácter de texto', 'caracteres de texto'),
    images > 0 && plural(images, 'foto', 'fotos'),
    videos > 0 && plural(videos, 'video', 'videos'),
  ].filter(Boolean).join(' · ')
  const AudienceIcon = post.audience === 'followers' ? Users : Globe
  const url = `${window.location.origin}/posts/${post.id}`

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(url)
      toast.success('Enlace copiado.')
    } catch {
      toast.error('No se pudo copiar el enlace.')
    }
  }

  return (
    <Sheet open onOpenChange={(open) => !open && onClose()} title="Información de la publicación">
      <div className="grid gap-5 px-5 pb-5">
        <dl className="grid gap-4">
          <Row icon={UserRound} label="Publicada por">
            <Link to={`/profile/${post.author.id}`} onClick={onClose} className="inline-flex items-center gap-2 font-semibold text-slate-900 hover:underline">
              <UserAvatar user={post.author} size="sm" />
              {post.author.name}
            </Link>
          </Row>
          <Row icon={CalendarClock} label="Fecha de publicación">
            {formatFullDateTime(post.created_at)} <span className="text-slate-500">({formatRelative(post.created_at)})</span>
          </Row>
          <Row icon={PencilLine} label="Última edición">
            {post.edited_at ? <>{formatFullDateTime(post.edited_at)} <span className="text-slate-500">({formatRelative(post.edited_at)})</span></> : 'Sin editar'}
          </Row>
          <Row icon={AudienceIcon} label="Privacidad">
            <span className="font-semibold">{AUDIENCE_LABELS[post.audience]}</span>
            <span className="block text-slate-500">{AUDIENCE_HELP[post.audience]}</span>
          </Row>
          <Row icon={ImageIcon} label="Contenido">
            {content || 'Sin contenido'}
            {post.attachments.length > 0 && <span className="block text-slate-500">Archivos: {formatBytes(totalSize)} en total</span>}
          </Row>
          <Row icon={SmilePlus} label="Reacciones">{plural(post.reactions.total, 'reacción', 'reacciones')}</Row>
          <Row icon={MessageCircle} label="Comentarios">{plural(post.comments_count, 'comentario', 'comentarios')}</Row>
          <Row icon={Hash} label="Folio">
            <span className="tabular-nums">#{post.id}</span>
          </Row>
        </dl>

        <Button variant="outline" onClick={() => void copyLink()}>
          <Link2 className="size-4" aria-hidden /> Copiar enlace
        </Button>
      </div>
    </Sheet>
  )
}

function Row({ icon: Icon, label, children }: { icon: LucideIcon; label: string; children: ReactNode }) {
  return (
    <div className="flex gap-3">
      <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600">
        <Icon className="size-4" aria-hidden />
      </span>
      <div className="min-w-0 flex-1">
        <dt className="text-xs font-medium text-slate-500">{label}</dt>
        <dd className="text-sm break-words text-slate-800">{children}</dd>
      </div>
    </div>
  )
}
