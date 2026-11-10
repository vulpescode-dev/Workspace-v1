import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { Plus, Search, ShoppingBag } from 'lucide-react'
import { useState } from 'react'
import { useSearchParams } from 'react-router'

import { EmptyState } from '@/components/feedback/EmptyState'
import { Skeleton, SkeletonGroup } from '@/components/feedback/Skeleton'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Tabs } from '@/components/ui/Tabs'
import { useCan } from '@/features/accounts/hooks/useCan'
import { useMe } from '@/features/accounts/hooks/useMe'
import { marketplaceApi, marketplaceKeys } from '@/features/marketplace/api/marketplace.api'
import { ListingCard } from '@/features/marketplace/components/ListingCard'
import { ListingFormSheet } from '@/features/marketplace/components/ListingFormSheet'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { cn } from '@/lib/cn'

/**
 * /marketplace — compra-venta entre colegas. Por omisión solo lo disponible; «Mis anuncios» muestra los
 * míos (vendidos incluidos). Búsqueda, categoría y pestaña en la URL (`?q=`, `?category=`, `?view=mine`, `?sold=1`).
 */
export function MarketplacePage() {
  useDocumentTitle('Marketplace')
  const { data: me } = useMe()
  const canSell = useCan()('marketplace.listings.create')
  const [params, setParams] = useSearchParams()
  const [text, setText] = useState(params.get('q') ?? '')
  const q = useDebouncedValue(text.trim(), 300)
  const category = params.get('category') ?? ''
  const mine = params.get('view') === 'mine'
  const withSold = params.get('sold') === '1'
  const filters = { q, category, seller: mine ? me?.id : undefined, status: mine || withSold ? undefined : ('available' as const) }
  const [selling, setSelling] = useState(false)

  const categories = useQuery({ queryKey: marketplaceKeys.categories(), queryFn: marketplaceApi.categories, staleTime: 10 * 60_000 })
  const list = useInfiniteQuery({
    queryKey: marketplaceKeys.list(filters),
    queryFn: ({ pageParam }) => marketplaceApi.list(filters, pageParam),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page < last.total_pages ? last.page + 1 : undefined),
    placeholderData: (previous) => previous,
    enabled: !mine || Boolean(me),
  })

  function update(next: Record<string, string>) {
    const merged = new URLSearchParams(params)
    Object.entries(next).forEach(([key, value]) => (value ? merged.set(key, value) : merged.delete(key)))
    setParams(merged, { replace: true })
  }

  const items = list.data?.pages.flatMap((page) => page.results) ?? []
  const filtering = Boolean(q || category)

  return (
    <>
      <PageHeader
        title="Marketplace"
        description="Compra y vende entre colegas: lo que ya no usas le sirve a alguien más."
        actions={canSell && <Button onClick={() => setSelling(true)}><Plus className="size-4" aria-hidden /> Vender algo</Button>}
      />
      <Tabs
        label="Qué anuncios ver"
        options={[{ value: 'all', label: 'Todos' }, { value: 'mine', label: 'Mis anuncios' }]}
        value={mine ? 'mine' : 'all'}
        onChange={(value) => update({ view: value === 'mine' ? 'mine' : '' })}
        className="mb-4"
      />

      <Card className="mb-5 grid gap-3 p-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <label className="relative flex-1">
            <span className="sr-only">Buscar en el Marketplace</span>
            <Search className="pointer-events-none absolute top-1/2 left-3.5 size-5 -translate-y-1/2 text-slate-400" aria-hidden />
            <input
              type="search"
              value={text}
              onChange={(event) => { setText(event.target.value); update({ q: event.target.value.trim() }) }}
              placeholder="¿Qué buscas?"
              className="h-11 w-full rounded-xl border border-slate-200 pr-3 pl-11 text-base placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm"
            />
          </label>
          {!mine && (
            <label className="flex shrink-0 cursor-pointer items-center gap-2 px-1 text-sm font-medium text-slate-600 select-none">
              <input type="checkbox" checked={withSold} onChange={(event) => update({ sold: event.target.checked ? '1' : '' })} className="size-4 rounded accent-brand-500" />
              Mostrar vendidos
            </label>
          )}
        </div>
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
        <SkeletonGroup label="Cargando anuncios" className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }, (_, index) => (
            <Card key={index} className="overflow-hidden">
              <Skeleton className="aspect-square rounded-none" />
              <div className="grid gap-2 p-3"><Skeleton className="h-5 w-16" /><Skeleton className="h-4 w-full" /><Skeleton className="h-3 w-2/3" /></div>
            </Card>
          ))}
        </SkeletonGroup>
      ) : list.isError ? (
        <Card><EmptyState icon={ShoppingBag} title="No se pudieron cargar los anuncios" action={<Button variant="outline" onClick={() => void list.refetch()}>Reintentar</Button>} /></Card>
      ) : items.length === 0 ? (
        <Card>
          <EmptyState
            icon={ShoppingBag}
            title={filtering ? 'Nada coincide con tu búsqueda' : mine ? 'Aún no vendes nada' : 'Todavía no hay anuncios'}
            description={filtering ? 'Prueba con otras palabras o con otra categoría.' : 'Publica lo que ya no usas: alguien de la empresa puede necesitarlo.'}
            action={!filtering && canSell ? <Button onClick={() => setSelling(true)}>Vender algo</Button> : undefined}
          />
        </Card>
      ) : (
        <div className={cn('grid grid-cols-2 gap-3 transition-opacity duration-150 sm:gap-4 md:grid-cols-3 xl:grid-cols-3', list.isPlaceholderData && 'opacity-60')}>
          {items.map((listing) => <ListingCard key={listing.id} listing={listing} />)}
        </div>
      )}
      {list.hasNextPage && (
        <Button variant="outline" className="mx-auto mt-5 flex" loading={list.isFetchingNextPage} onClick={() => void list.fetchNextPage()}>Ver más anuncios</Button>
      )}

      {selling && <ListingFormSheet categories={categories.data ?? []} onClose={() => setSelling(false)} />}
    </>
  )
}
