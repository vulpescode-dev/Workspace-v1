import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { ArrowLeft, FileX, MessageCircle, Pencil, Trash2 } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'

import { useCan } from '@/features/accounts/hooks/useCan'
import { EmptyState } from '@/components/feedback/EmptyState'
import { Skeleton } from '@/components/feedback/Skeleton'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { articleCommentSource, blogApi, blogKeys, type ArticleDetail } from '@/features/blog/api/blog.api'
import { ArticleCover } from '@/features/blog/components/ArticleCover'
import { ArticleReactions } from '@/features/blog/components/ArticleReactions'
import { ArticleStatusBadge } from '@/features/blog/components/ArticleStatusBadge'
import { CommentsPanel } from '@/features/comments/components/CommentsPanel'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { getErrorMessage } from '@/lib/api/errors'
import { formatFullDateTime, formatLongDate } from '@/lib/format'

/** Minutos de lectura (≈200 palabras por minuto), del HTML ya limpio. */
function readingMinutes(html: string) {
  const words = html.replace(/<[^>]+>/g, ' ').split(/\s+/).filter(Boolean).length
  return Math.max(1, Math.round(words / 200))
}

/**
 * /blog/:id — una noticia: portada, título, autor, contenido (HTML limpio del servidor), reacciones y
 * comentarios en la misma página. Quien la escribió puede editarla o eliminarla y ve sus borradores.
 */
export function ArticlePage() {
  const can = useCan()
  const id = Number(useParams().articleId)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const article = useQuery({ queryKey: blogKeys.detail(id), queryFn: () => blogApi.get(id), enabled: Number.isInteger(id) })
  useDocumentTitle(article.data?.title ?? 'Noticia')

  const remove = useMutation({
    mutationFn: () => blogApi.remove(id),
    onSuccess: () => {
      toast('Noticia eliminada.')
      void queryClient.invalidateQueries({ queryKey: blogKeys.lists() })
      navigate('/blog', { replace: true })
    },
    onError: (error) => toast.error(getErrorMessage(error, 'No se pudo eliminar.')),
  })

  const back = (
    <Link to="/blog" className="inline-flex w-fit items-center gap-2 rounded-lg text-sm font-semibold text-slate-500 hover:text-slate-800">
      <ArrowLeft className="size-4" aria-hidden /> Noticias
    </Link>
  )

  if (article.isPending) {
    return (
      <div className="grid w-full gap-4">
        {back}
        <Card className="overflow-hidden">
          <Skeleton className="aspect-video rounded-none" />
          <div className="grid gap-3 p-5 sm:p-8"><Skeleton className="h-8 w-3/4" /><Skeleton className="h-4 w-1/3" /><Skeleton className="mt-4 h-4 w-full" /><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-2/3" /></div>
        </Card>
      </div>
    )
  }
  if (article.isError) {
    const gone = isAxiosError(article.error) && article.error.response?.status === 404
    return (
      <div className="grid w-full gap-4">
        {back}
        <Card>
          <EmptyState
            icon={FileX}
            title={gone ? 'Esta noticia no está disponible' : 'No se pudo cargar la noticia'}
            description={gone ? 'Puede que se haya eliminado o que todavía no se publique.' : undefined}
            action={gone ? undefined : <Button variant="outline" onClick={() => void article.refetch()}>Reintentar</Button>}
          />
        </Card>
      </div>
    )
  }

  const data = article.data
  const published = data.status === 'published' && !data.is_scheduled
  const date = data.published_at ?? data.updated_at
  const canEdit = data.is_mine || can('blog.articles.update.all')
  const canDelete = data.is_mine || can('blog.articles.delete.all')
  const setCount = (count: number) =>
    queryClient.setQueryData<ArticleDetail>(blogKeys.detail(id), (current) => current && { ...current, comments_count: count })

  return (
    <div className="grid w-full gap-4">
      {back}
      <Card className="overflow-hidden">
        <article>
          {data.cover_url && <ArticleCover url={data.cover_url} />}
          <header className="grid gap-4 px-5 pt-6 sm:px-10 sm:pt-10">
            <div className="flex flex-wrap items-center gap-2">
              {data.category && (
                <Link to={`/blog?category=${data.category.slug}`} className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-semibold text-brand-700 hover:bg-brand-100">
                  {data.category.name}
                </Link>
              )}
              <ArticleStatusBadge article={data} />
              {data.is_scheduled && data.published_at && <span className="text-xs text-slate-500">Se publica el {formatFullDateTime(data.published_at)}</span>}
            </div>
            <h1 className="text-3xl leading-tight font-bold text-slate-900 sm:text-4xl">{data.title}</h1>
            {data.excerpt && <p className="text-lg text-slate-600">{data.excerpt}</p>}
            <div className="flex flex-wrap items-center gap-3 border-y border-slate-100 py-3">
              <Link to={`/profile/${data.author.id}`} className="flex min-w-0 items-center gap-2.5">
                <UserAvatar user={data.author} />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-semibold text-slate-900 hover:underline">{data.author.name}</span>
                  <span className="block text-xs text-slate-500">
                    <time dateTime={date} title={formatFullDateTime(date)}>{formatLongDate(date)}</time> · {readingMinutes(data.body)} min de lectura
                  </span>
                </span>
              </Link>
              {/* Lo propio, o lo ajeno con «update.all» / «delete.all» (moderación). */}
              {(canEdit || canDelete) && (
                <div className="ml-auto flex gap-1">
                  {canEdit && <Button variant="ghost" size="sm" onClick={() => navigate(`/blog/${id}/edit`)}><Pencil className="size-4" aria-hidden /> Editar</Button>}
                  {canDelete && (
                    <Button variant="ghost" size="sm" aria-label="Eliminar noticia" loading={remove.isPending}
                      onClick={() => window.confirm('¿Eliminar esta noticia? Se quitarán también sus comentarios y reacciones.') && remove.mutate()}>
                      <Trash2 className="size-4 text-red-500" aria-hidden />
                    </Button>
                  )}
                </div>
              )}
            </div>
          </header>

          {data.body ? (
            // HTML limpiado por el servidor con lista permitida (nh3) al guardar: sin scripts ni atributos peligrosos.
            <div className="ws-article px-5 py-6 sm:px-10 sm:py-8" dangerouslySetInnerHTML={{ __html: data.body }} />
          ) : (
            <p className="px-5 py-8 text-sm text-slate-500 italic sm:px-10">Esta noticia aún no tiene contenido.</p>
          )}

          {published && (
            <footer className="border-t border-slate-100 px-5 py-4 sm:px-10">
              <ArticleReactions article={data} />
            </footer>
          )}
        </article>
      </Card>

      {published ? (
        <Card className="overflow-hidden">
          <h2 className="flex items-center gap-2 border-b border-slate-100 px-5 py-4 text-base font-bold text-slate-900">
            <MessageCircle className="size-5 text-slate-400" aria-hidden />
            {data.comments_count > 0 ? `${data.comments_count} ${data.comments_count === 1 ? 'comentario' : 'comentarios'}` : 'Comentarios'}
          </h2>
          <CommentsPanel source={articleCommentSource(id)} onCountChange={setCount} />
        </Card>
      ) : (
        <p className="text-center text-sm text-slate-500">Las reacciones y los comentarios se abren cuando la noticia se publique.</p>
      )}
    </div>
  )
}
