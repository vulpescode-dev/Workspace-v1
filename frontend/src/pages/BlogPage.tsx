import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { Newspaper, PenSquare, Search } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'

import { EmptyState } from '@/components/feedback/EmptyState'
import { Skeleton, SkeletonGroup } from '@/components/feedback/Skeleton'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Tabs } from '@/components/ui/Tabs'
import { blogApi, blogKeys } from '@/features/blog/api/blog.api'
import { ArticleCard } from '@/features/blog/components/ArticleCard'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { cn } from '@/lib/cn'

/**
 * /blog — Noticias: la más reciente destacada y las demás en cuadrícula. Búsqueda y categoría en la URL
 * (`?q=`, `?category=<slug>`). Quien puede escribir ve además «Mis artículos» (borradores y programados).
 */
export function BlogPage() {
  useDocumentTitle('Noticias')
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const [text, setText] = useState(params.get('q') ?? '')
  const q = useDebouncedValue(text.trim(), 300)
  const category = params.get('category') ?? ''
  const mine = params.get('view') === 'mine'
  const filters = { category, q, mine }

  const permissions = useQuery({ queryKey: blogKeys.permissions(), queryFn: blogApi.permissions, staleTime: 5 * 60_000 })
  const categories = useQuery({ queryKey: blogKeys.categories(), queryFn: blogApi.categories, staleTime: 10 * 60_000 })
  const list = useInfiniteQuery({
    queryKey: blogKeys.list(filters),
    queryFn: ({ pageParam }) => blogApi.list(filters, pageParam),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page < last.total_pages ? last.page + 1 : undefined),
    placeholderData: (previous) => previous,
  })

  function update(next: Record<string, string>) {
    const merged = new URLSearchParams(params)
    Object.entries(next).forEach(([key, value]) => (value ? merged.set(key, value) : merged.delete(key)))
    setParams(merged, { replace: true })
  }

  const canWrite = permissions.data?.can_write ?? false
  const items = list.data?.pages.flatMap((page) => page.results) ?? []
  const filtering = Boolean(q || category)
  // La más reciente va destacada solo en la portada de Noticias (sin filtros).
  const [featured, ...rest] = !mine && !filtering ? items : [undefined, ...items]

  return (
    <>
      <PageHeader
        title="Noticias"
        description="Lo que pasa en la empresa: anuncios, logros, celebraciones y más."
        actions={canWrite && <Button onClick={() => navigate('/blog/new')}><PenSquare className="size-4" aria-hidden /> Escribir noticia</Button>}
      />
      {canWrite && (
        <Tabs
          label="Qué noticias ver"
          options={[{ value: 'all', label: 'Publicadas' }, { value: 'mine', label: 'Mis artículos' }]}
          value={mine ? 'mine' : 'all'}
          onChange={(value) => update({ view: value === 'mine' ? 'mine' : '' })}
          className="mb-4"
        />
      )}

      <Card className="mb-5 grid gap-3 p-3">
        <label className="relative">
          <span className="sr-only">Buscar noticias</span>
          <Search className="pointer-events-none absolute top-1/2 left-3.5 size-5 -translate-y-1/2 text-slate-400" aria-hidden />
          <input
            type="search"
            value={text}
            onChange={(event) => { setText(event.target.value); update({ q: event.target.value.trim() }) }}
            placeholder="Buscar por título o resumen"
            className="h-11 w-full rounded-xl border border-slate-200 pr-3 pl-11 text-base placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm"
          />
        </label>
        {(categories.data?.length ?? 0) > 0 && (
          <div className="flex gap-2 overflow-x-auto [scrollbar-width:none]" role="group" aria-label="Categorías">
            {[{ id: 0, name: 'Todas', slug: '' }, ...categories.data!].map((item) => {
              const active = category === item.slug
              return (
                <button
                  key={item.id}
                  type="button"
                  aria-pressed={active}
                  onClick={() => update({ category: item.slug })}
                  className={cn('pressable h-8 shrink-0 rounded-full px-3.5 text-sm font-semibold transition-colors duration-150', active ? 'bg-brand-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200')}
                >
                  {item.name}
                </button>
              )
            })}
          </div>
        )}
      </Card>

      {list.isPending ? (
        <ArticleGridSkeleton />
      ) : list.isError ? (
        <Card><EmptyState icon={Newspaper} title="No se pudieron cargar las noticias" action={<Button variant="outline" onClick={() => void list.refetch()}>Reintentar</Button>} /></Card>
      ) : items.length === 0 ? (
        <Card>
          <EmptyState
            icon={Newspaper}
            title={filtering ? 'Ninguna noticia coincide' : mine ? 'Aún no escribes noticias' : 'Todavía no hay noticias'}
            description={filtering ? 'Prueba con otras palabras o con otra categoría.' : mine ? 'Tus borradores y noticias programadas aparecerán aquí.' : 'Cuando se publique la primera, aparecerá aquí.'}
            action={!filtering && canWrite ? <Button onClick={() => navigate('/blog/new')}>Escribir noticia</Button> : undefined}
          />
        </Card>
      ) : (
        <div className={cn('grid gap-4 transition-opacity duration-150', list.isPlaceholderData && 'opacity-60')}>
          {featured && <ArticleCard article={featured} featured />}
          {rest.length > 0 && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {rest.map((article) => article && <ArticleCard key={article.id} article={article} />)}
            </div>
          )}
        </div>
      )}
      {list.hasNextPage && (
        <Button variant="outline" className="mx-auto mt-5 flex" loading={list.isFetchingNextPage} onClick={() => void list.fetchNextPage()}>Ver más noticias</Button>
      )}
    </>
  )
}

function ArticleGridSkeleton() {
  return (
    <SkeletonGroup label="Cargando noticias" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }, (_, index) => (
        <Card key={index} className="overflow-hidden">
          <Skeleton className="aspect-video rounded-none" />
          <div className="grid gap-2 p-4"><Skeleton className="h-4 w-20" /><Skeleton className="h-5 w-full" /><Skeleton className="h-4 w-2/3" /></div>
        </Card>
      ))}
    </SkeletonGroup>
  )
}
