import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, ImagePlus, Lock, Trash2 } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'

import { useCan } from '@/features/accounts/hooks/useCan'
import { EmptyState } from '@/components/feedback/EmptyState'
import { Skeleton } from '@/components/feedback/Skeleton'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Field } from '@/components/ui/Field'
import { blogApi, blogKeys, type ArticleDetail } from '@/features/blog/api/blog.api'
import { ArticleCover } from '@/features/blog/components/ArticleCover'
import { RichTextEditor } from '@/features/blog/components/RichTextEditor'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { getErrorMessage } from '@/lib/api/errors'
import { cn } from '@/lib/cn'
import { toWebp } from '@/lib/media/to-webp'

type Mode = 'draft' | 'now' | 'schedule'
const MODES: { value: Mode; label: string }[] = [
  { value: 'draft', label: 'Borrador' },
  { value: 'now', label: 'Publicar ahora' },
  { value: 'schedule', label: 'Programar' },
]
const selectClass = 'h-12 w-full rounded-xl border border-slate-200 bg-surface px-3 text-base text-slate-900 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm'

/** «2026-11-08T09:00» (lo que usa `<input type="datetime-local">`) en hora local. */
function toLocalInput(iso: string) {
  const date = new Date(iso)
  return new Date(date.getTime() - date.getTimezoneOffset() * 60_000).toISOString().slice(0, 16)
}

/** /blog/new y /blog/:id/edit — cargan lo necesario y muestran el formulario. */
export function ArticleEditorPage() {
  const can = useCan()
  const params = useParams()
  const id = params.articleId ? Number(params.articleId) : null
  const permissions = useQuery({ queryKey: blogKeys.permissions(), queryFn: blogApi.permissions, staleTime: 5 * 60_000, enabled: id === null })
  const article = useQuery({ queryKey: blogKeys.detail(id ?? 0), queryFn: () => blogApi.get(id!), enabled: id !== null })
  const categories = useQuery({ queryKey: blogKeys.categories(), queryFn: blogApi.categories, staleTime: 10 * 60_000 })
  useDocumentTitle(id ? 'Editar noticia' : 'Escribir noticia')

  const back = (
    <Link to={id ? `/blog/${id}` : '/blog'} className="inline-flex w-fit items-center gap-2 rounded-lg text-sm font-semibold text-slate-500 hover:text-slate-800">
      <ArrowLeft className="size-4" aria-hidden /> {id ? 'Volver a la noticia' : 'Noticias'}
    </Link>
  )
  const loading = (id ? article.isPending : permissions.isPending) || categories.isPending
  const blocked = id ? article.isError || (article.data && !article.data.is_mine && !can('blog.articles.update.all')) : permissions.data && !permissions.data.can_write

  return (
    <div className="grid w-full gap-4">
      {back}
      {loading ? (
        <Card className="grid gap-4 p-5 sm:p-8"><Skeleton className="aspect-video" /><Skeleton className="h-10 w-3/4" /><Skeleton className="h-64" /></Card>
      ) : blocked ? (
        <Card>
          <EmptyState icon={Lock} title={id ? 'No puedes editar esta noticia' : 'No tienes permiso para escribir noticias'} description={id ? 'Solo quien la escribió puede cambiarla.' : 'Pide a Comunicación o a Soporte TI que te den acceso.'} />
        </Card>
      ) : (
        <ArticleForm article={article.data} categories={categories.data ?? []} />
      )}
    </div>
  )
}

function ArticleForm({ article, categories }: { article?: ArticleDetail; categories: { id: number; name: string }[] }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const coverInput = useRef<HTMLInputElement>(null)
  const [title, setTitle] = useState(article?.title ?? '')
  const [excerpt, setExcerpt] = useState(article?.excerpt ?? '')
  const [category, setCategory] = useState(article?.category?.id ?? 0)
  const [body, setBody] = useState(article?.body ?? '')
  const initialMode: Mode = !article || article.status === 'draft' ? 'draft' : article.is_scheduled ? 'schedule' : 'now'
  const [mode, setMode] = useState<Mode>(initialMode)
  const [scheduledFor, setScheduledFor] = useState(article?.is_scheduled && article.published_at ? toLocalInput(article.published_at) : '')
  // Portada: `undefined` = sin cambios, `null` = quitarla, o la nueva (ya en WebP) con su vista previa local.
  const [cover, setCover] = useState<{ file: File; preview: string } | null | undefined>(undefined)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => () => { if (cover) URL.revokeObjectURL(cover.preview) }, [cover])

  // La categoría actual puede estar desactivada: se sigue mostrando para no perderla sin querer.
  const options = article?.category && !categories.some((item) => item.id === article.category!.id) ? [article.category, ...categories] : categories
  const hasCover = Boolean(cover) || (cover === undefined && Boolean(article?.cover_url))

  const save = useMutation({
    mutationFn: () => {
      const form = new FormData()
      form.append('title', title.trim())
      form.append('excerpt', excerpt.trim())
      form.append('body', body)
      form.append('category', category ? String(category) : '')
      form.append('status', mode === 'draft' ? 'draft' : 'published')
      if (mode === 'schedule') form.append('published_at', new Date(scheduledFor).toISOString())
      // «Publicar ahora» sobre algo que no estaba publicado (o estaba programado): la fecha la pone el servidor.
      else if (mode === 'now' && initialMode !== 'now') form.append('published_at', '')
      if (cover) form.append('cover', cover.file)
      if (cover === null) form.append('remove_cover', 'true')
      return article ? blogApi.update(article.id, form) : blogApi.create(form)
    },
    onSuccess: (saved) => {
      queryClient.setQueryData(blogKeys.detail(saved.id), saved)
      void queryClient.invalidateQueries({ queryKey: blogKeys.lists() })
      toast.success(mode === 'draft' ? 'Borrador guardado.' : mode === 'schedule' ? 'Noticia programada.' : article?.status === 'published' && initialMode === 'now' ? 'Cambios publicados.' : 'Noticia publicada.')
      navigate(`/blog/${saved.id}`, { replace: Boolean(article) })
    },
    onError: (err) => setError(getErrorMessage(err, 'No se pudo guardar la noticia.')),
  })

  async function pickCover(file: File | undefined) {
    if (!file) return
    try {
      const webp = await toWebp(file, { maxSide: 1920 })
      setCover({ file: webp, preview: URL.createObjectURL(webp) })
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo preparar la imagen.')
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!title.trim()) return setError('Escribe un título.')
    if (mode !== 'draft' && !body) return setError('Escribe el contenido antes de publicar.')
    if (mode === 'schedule' && (!scheduledFor || new Date(scheduledFor) <= new Date())) return setError('Elige una fecha y hora futuras para programarla.')
    setError(null)
    save.mutate()
  }

  const submitLabel = mode === 'draft' ? 'Guardar borrador' : mode === 'schedule' ? 'Programar' : initialMode === 'now' ? 'Guardar cambios' : 'Publicar'

  return (
    <form onSubmit={submit} className="grid gap-4">
      <Card className="overflow-hidden">
        <div className="relative">
          {hasCover ? <ArticleCover url={cover === undefined ? article?.cover_url : undefined} src={cover?.preview} /> : (
            <button type="button" onClick={() => coverInput.current?.click()}
              className="flex aspect-[3/1] w-full flex-col items-center justify-center gap-2 bg-slate-50 text-sm font-semibold text-slate-500 transition-colors duration-150 hover:bg-brand-50/50 hover:text-brand-700">
              <ImagePlus className="size-7" aria-hidden /> Agregar portada
              <span className="text-xs font-normal text-slate-400">Horizontal (16:9) se ve mejor</span>
            </button>
          )}
          {hasCover && (
            <div className="absolute right-3 bottom-3 flex gap-2">
              <Button size="sm" variant="outline" onClick={() => coverInput.current?.click()}><ImagePlus className="size-4" aria-hidden /> Cambiar</Button>
              <Button size="sm" variant="outline" aria-label="Quitar portada" onClick={() => setCover(null)}><Trash2 className="size-4 text-red-500" aria-hidden /></Button>
            </div>
          )}
          <input ref={coverInput} type="file" accept="image/*" hidden onChange={(event) => { void pickCover(event.target.files?.[0]); event.target.value = '' }} />
        </div>

        <div className="grid gap-4 p-5 sm:p-8">
          <label className="grid gap-1">
            <span className="sr-only">Título</span>
            <textarea
              value={title}
              onChange={(event) => setTitle(event.target.value.replace(/\n/g, ' '))}
              maxLength={200}
              rows={1}
              placeholder="Título de la noticia"
              className="field-sizing-content resize-none bg-transparent font-display text-3xl leading-tight font-bold text-slate-900 placeholder:text-slate-300 focus:outline-none sm:text-4xl"
            />
          </label>
          <label className="grid gap-1">
            <span className="sr-only">Resumen</span>
            <textarea
              value={excerpt}
              onChange={(event) => setExcerpt(event.target.value.replace(/\n/g, ' '))}
              maxLength={300}
              rows={1}
              placeholder="Resumen corto para la tarjeta (opcional)"
              className="field-sizing-content resize-none bg-transparent text-lg text-slate-600 placeholder:text-slate-300 focus:outline-none"
            />
          </label>
          <RichTextEditor value={body} onChange={setBody} label="Contenido de la noticia" />
        </div>
      </Card>

      {/* Fija abajo solo en escritorio: en el teléfono taparía un tercio del texto mientras se escribe. */}
      <Card className="z-20 grid gap-4 p-4 sm:p-5 lg:sticky lg:bottom-4">
        {error && <Alert tone="error">{error}</Alert>}
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Categoría">
            {({ invalid, ...props }) => (
              <select {...props} aria-invalid={invalid || undefined} value={category} onChange={(event) => setCategory(Number(event.target.value))} className={selectClass}>
                <option value={0}>Sin categoría</option>
                {options.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
              </select>
            )}
          </Field>
          <fieldset className="grid gap-1.5">
            <legend className="mb-1.5 text-sm font-semibold text-slate-700">Estado</legend>
            <div className="grid grid-cols-3 gap-1 rounded-xl bg-slate-100 p-1">
              {MODES.map((option) => (
                <button key={option.value} type="button" aria-pressed={mode === option.value} onClick={() => setMode(option.value)}
                  className={cn('h-10 rounded-lg px-1 text-sm leading-tight font-semibold transition-colors duration-150', mode === option.value ? 'bg-surface text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800')}>
                  {option.label}
                </button>
              ))}
            </div>
          </fieldset>
        </div>
        {mode === 'schedule' && (
          <Field label="Se publica el" hint="Aparecerá sola en Noticias a esa hora. Mientras tanto solo tú la ves.">
            {({ invalid, ...props }) => (
              <input {...props} aria-invalid={invalid || undefined} type="datetime-local" value={scheduledFor} onChange={(event) => setScheduledFor(event.target.value)} className={selectClass} />
            )}
          </Field>
        )}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => navigate(article ? `/blog/${article.id}` : '/blog')}>Cancelar</Button>
          <Button type="submit" loading={save.isPending}>{submitLabel}</Button>
        </div>
      </Card>
    </form>
  )
}
