import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { ArrowLeft, CheckCircle2, ChevronLeft, ChevronRight, Expand, FileX, Images, MessageCircle, Pencil, RotateCcw, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'

import { useCan } from '@/features/accounts/hooks/useCan'
import { EmptyState } from '@/components/feedback/EmptyState'
import { Skeleton } from '@/components/feedback/Skeleton'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { formatPrice, marketplaceApi, marketplaceKeys, type Listing } from '@/features/marketplace/api/marketplace.api'
import { ListingDescription } from '@/features/marketplace/components/ListingDescription'
import { ListingFormSheet } from '@/features/marketplace/components/ListingFormSheet'
import { ListingPhoto } from '@/features/marketplace/components/ListingPhoto'
import { SellerListings } from '@/features/marketplace/components/SellerListings'
import { PostGallery } from '@/features/posts/components/PostGallery'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { getErrorMessage } from '@/lib/api/errors'
import { cn } from '@/lib/cn'
import { formatFullDateTime, formatRelative } from '@/lib/format'

/**
 * /marketplace/:id — fotos (tocar abre la galería a pantalla completa), precio, título y quién lo vende en una
 * ficha fija; la descripción (a veces larga y detallada) va aparte, a lo ancho, debajo de las fotos; más
 * otros anuncios del mismo vendedor. Quien lo publicó lo edita, lo marca como vendido (o disponible otra
 * vez) o lo elimina.
 */
export function ListingPage() {
  const can = useCan()
  const id = Number(useParams().listingId)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const listing = useQuery({ queryKey: marketplaceKeys.detail(id), queryFn: () => marketplaceApi.get(id), enabled: Number.isInteger(id) })
  const [photo, setPhoto] = useState(0)
  const [gallery, setGallery] = useState<number | null>(null)
  const [editing, setEditing] = useState(false)
  const categories = useQuery({ queryKey: marketplaceKeys.categories(), queryFn: marketplaceApi.categories, staleTime: 10 * 60_000, enabled: editing })
  useDocumentTitle(listing.data?.title ?? 'Anuncio')
  // Misma consulta que «Más de…» (React Query la comparte): de aquí sale cuántas cosas vende.
  const sellerFilters = { seller: listing.data?.seller.id, status: 'available' as const }
  const sellerListings = useQuery({
    queryKey: marketplaceKeys.list(sellerFilters), queryFn: () => marketplaceApi.list(sellerFilters, 1),
    enabled: !!listing.data && !listing.data.is_mine, staleTime: 60_000,
  })

  const saved = (data: Listing) => {
    queryClient.setQueryData(marketplaceKeys.detail(id), data)
    void queryClient.invalidateQueries({ queryKey: marketplaceKeys.lists() })
  }
  const toggleSold = useMutation({
    mutationFn: (status: Listing['status']) => marketplaceApi.update(id, { status }),
    onSuccess: (data) => { saved(data); toast.success(data.status === 'sold' ? '¡Felicidades por la venta!' : 'El anuncio está disponible otra vez.') },
    onError: (error) => toast.error(getErrorMessage(error, 'No se pudo cambiar el estatus.')),
  })
  const remove = useMutation({
    mutationFn: () => marketplaceApi.remove(id),
    onSuccess: () => {
      toast('Anuncio eliminado.')
      void queryClient.invalidateQueries({ queryKey: marketplaceKeys.lists() })
      navigate('/marketplace', { replace: true })
    },
    onError: (error) => toast.error(getErrorMessage(error, 'No se pudo eliminar.')),
  })

  const back = (
    <Link to="/marketplace" className="group inline-flex w-fit items-center gap-2 rounded-lg text-sm font-semibold text-slate-500 transition-colors duration-150 hover:text-slate-800">
      <ArrowLeft className="size-4 transition-transform duration-200 ease-(--ease-out) group-hover:-translate-x-0.5" aria-hidden /> Marketplace
    </Link>
  )

  if (listing.isPending) {
    return (
      <div className="grid gap-4">
        {back}
        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] lg:gap-8">
          <Skeleton className="aspect-square rounded-3xl sm:aspect-[4/3]" />
          <Card className="grid content-start gap-4 p-5 lg:p-6">
            <Skeleton className="h-6 w-28" /><Skeleton className="h-8 w-3/4" /><Skeleton className="h-10 w-32" /><Skeleton className="mt-2 h-32 rounded-2xl" /><Skeleton className="h-16" />
          </Card>
        </div>
      </div>
    )
  }
  if (listing.isError) {
    const gone = isAxiosError(listing.error) && listing.error.response?.status === 404
    return (
      <div className="grid gap-4">
        {back}
        <Card>
          <EmptyState icon={FileX} title={gone ? 'Este anuncio ya no está disponible' : 'No se pudo cargar el anuncio'} description={gone ? 'Puede que quien lo publicó lo haya eliminado.' : undefined}
            action={gone ? undefined : <Button variant="outline" onClick={() => void listing.refetch()}>Reintentar</Button>} />
        </Card>
      </div>
    )
  }

  const data = listing.data
  const sold = data.status === 'sold'
  const images = data.images
  const index = Math.min(photo, Math.max(images.length - 1, 0))
  const current = images[index]
  const many = images.length > 1
  const step = (delta: number) => setPhoto((index + delta + images.length) % images.length)
  const firstName = data.seller.name.split(' ')[0]
  const canModerateEdit = can('marketplace.listings.update.all')
  const canModerateDelete = can('marketplace.listings.delete.all')
  const onSale = sellerListings.data?.count

  return (
    <div className="grid gap-10">
      <div className="grid gap-4">
        {back}
        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] lg:gap-8">
          {/* Escritorio: fotos y descripción en la columna ancha; la ficha (precio, vendedor, contactar) a la
              derecha se queda fija al bajar, así una descripción larga nunca aleja el botón de contactar.
              Teléfono: fotos › ficha › descripción. */}
          <div className="grid min-w-0 gap-3 lg:col-start-1 lg:row-start-1">
            <div className="group relative overflow-hidden rounded-3xl bg-slate-100 ring-1 ring-slate-900/5"
              onKeyDown={(event) => {
                if (!many) return
                if (event.key === 'ArrowLeft') step(-1)
                if (event.key === 'ArrowRight') step(1)
              }}>
              <button type="button" onClick={() => current && setGallery(index)} disabled={!current} aria-label={current ? 'Ver fotos en grande' : undefined}
                className="block w-full cursor-zoom-in disabled:cursor-default">
                <ListingPhoto url={current?.url} alt={data.title} className={cn('aspect-square sm:aspect-[4/3]', sold && 'grayscale-[60%]')} />
              </button>

              {sold && <span className="pointer-events-none absolute top-4 left-4 rounded-full bg-slate-900/80 px-3 py-1 text-sm font-bold text-white backdrop-blur-sm">Vendido</span>}
              {current && (
                <span aria-hidden className="pointer-events-none absolute top-4 right-4 grid size-9 place-items-center rounded-full bg-white/85 text-slate-700 opacity-0 shadow-sm backdrop-blur-sm transition-opacity duration-200 group-hover:opacity-100">
                  <Expand className="size-4" />
                </span>
              )}
              {many && (
                <>
                  <PhotoArrow side="left" onClick={() => step(-1)} />
                  <PhotoArrow side="right" onClick={() => step(1)} />
                  <span className="pointer-events-none absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-slate-900/60 px-2.5 py-1 text-xs font-semibold text-white tabular-nums backdrop-blur-sm">
                    {index + 1} / {images.length}
                  </span>
                </>
              )}
            </div>

            {many && (
              <ul className="flex gap-2.5 overflow-x-auto p-1 [scrollbar-width:thin]" aria-label="Fotos">
                {images.map((image, i) => (
                  <li key={image.id} className="shrink-0">
                    <button type="button" onClick={() => setPhoto(i)} aria-label={`Foto ${i + 1}`} aria-current={i === index}
                      className={cn('pressable block overflow-hidden rounded-xl ring-2 ring-offset-2 ring-offset-canvas transition-[box-shadow,opacity,transform] duration-150',
                        i === index ? 'ring-brand-500' : 'opacity-60 ring-transparent hover:opacity-100')}>
                      <ListingPhoto url={image.url} className="size-16 sm:size-[4.5rem]" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Ficha */}
          <Card className="grid min-w-0 content-start gap-6 p-5 lg:sticky lg:top-24 lg:col-start-2 lg:row-span-2 lg:row-start-1 lg:p-6">
            <div className="grid gap-3">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className={cn('inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-semibold',
                  sold ? 'bg-slate-100 text-slate-500' : 'bg-emerald-50 text-emerald-700')}>
                  <span className={cn('size-1.5 rounded-full', sold ? 'bg-slate-400' : 'bg-emerald-500')} aria-hidden />
                  {sold ? 'Vendido' : 'Disponible'}
                </span>
                {data.category && (
                  <Link to={`/marketplace?category=${data.category.slug}`}
                    className="rounded-full bg-slate-100 px-2.5 py-1 font-medium text-slate-600 transition-colors duration-150 hover:bg-slate-200 hover:text-slate-800">
                    {data.category.name}
                  </Link>
                )}
              </div>
              <h1 className="text-2xl leading-tight font-bold text-balance break-words text-slate-900 sm:text-[1.75rem]">{data.title}</h1>
              <p className={cn('font-display text-4xl font-bold tracking-tight tabular-nums', sold ? 'text-slate-400 line-through decoration-2' : 'text-slate-900')}>
                {formatPrice(data.price)}
              </p>
              <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-500">
                <time dateTime={data.created_at} title={formatFullDateTime(data.created_at)}>Publicado {formatRelative(data.created_at)}</time>
                {sold && data.sold_at && <span>Vendido {formatRelative(data.sold_at)}</span>}
                {images.length > 0 && (
                  <span className="inline-flex items-center gap-1"><Images className="size-3.5" aria-hidden />{images.length} {images.length === 1 ? 'foto' : 'fotos'}</span>
                )}
              </p>
            </div>

            {data.is_mine ? (
              <div className="grid gap-2 rounded-2xl bg-slate-50 p-3 sm:grid-cols-2 lg:grid-cols-1">
                <p className="px-1 text-xs font-semibold tracking-wide text-slate-500 uppercase sm:col-span-2 lg:col-span-1">Tu anuncio</p>
                {sold ? (
                  <Button variant="outline" loading={toggleSold.isPending} onClick={() => toggleSold.mutate('available')}><RotateCcw className="size-4" aria-hidden /> Disponible otra vez</Button>
                ) : (
                  <Button loading={toggleSold.isPending} onClick={() => toggleSold.mutate('sold')}><CheckCircle2 className="size-4" aria-hidden /> Marcar como vendido</Button>
                )}
                <Button variant="outline" onClick={() => setEditing(true)}><Pencil className="size-4" aria-hidden /> Editar</Button>
                <Button variant="ghost" className="text-red-600 hover:bg-red-50 hover:text-red-700 sm:col-span-2 lg:col-span-1" loading={remove.isPending}
                  onClick={() => window.confirm('¿Eliminar este anuncio? Dejará de verse para todos.') && remove.mutate()}>
                  <Trash2 className="size-4" aria-hidden /> Eliminar anuncio
                </Button>
              </div>
            ) : (
              <div className="grid gap-4 rounded-2xl border border-slate-200/80 p-4">
                <Link to={`/profile/${data.seller.id}`} className="group flex items-center gap-3 rounded-xl">
                  <UserAvatar user={data.seller} size="lg" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-slate-500">Lo vende</p>
                    <p className="truncate font-semibold text-slate-900 transition-colors duration-150 group-hover:text-brand-700">{data.seller.name}</p>
                    {onSale !== undefined && onSale > 0 && (
                      <p className="text-xs text-slate-500">{onSale} {onSale === 1 ? 'artículo' : 'artículos'} a la venta</p>
                    )}
                  </div>
                  <ChevronRight className="size-4 shrink-0 text-slate-400 transition-transform duration-200 ease-(--ease-out) group-hover:translate-x-0.5" aria-hidden />
                </Link>
                <Button className="w-full" variant={sold ? 'outline' : 'primary'} onClick={() => navigate(`/profile/${data.seller.id}`)}>
                  <MessageCircle className="size-4" aria-hidden /> Contactar a {firstName}
                </Button>
              </div>
            )}

            {/* Moderación: anuncios ajenos con «update.all» / «delete.all». */}
            {!data.is_mine && (canModerateEdit || canModerateDelete) && (
              <div className="grid gap-2 rounded-2xl bg-amber-50 p-3">
                <p className="px-1 text-xs font-semibold tracking-wide text-amber-800 uppercase">Moderación</p>
                {canModerateEdit && <Button variant="outline" onClick={() => setEditing(true)}><Pencil className="size-4" aria-hidden /> Editar anuncio</Button>}
                {canModerateDelete && (
                  <Button variant="ghost" className="text-red-600 hover:bg-red-50 hover:text-red-700" loading={remove.isPending}
                    onClick={() => window.confirm('¿Eliminar este anuncio de otra persona? Dejará de verse para todos.') && remove.mutate()}>
                    <Trash2 className="size-4" aria-hidden /> Eliminar anuncio
                  </Button>
                )}
              </div>
            )}
          </Card>

          {data.description && (
            <div className="min-w-0 lg:col-start-1 lg:row-start-2">
              <ListingDescription text={data.description} />
            </div>
          )}
        </div>
      </div>

      {!data.is_mine && <SellerListings seller={data.seller} excludeId={data.id} />}

      {gallery !== null && (
        <PostGallery attachments={images.map((image) => ({ id: image.id, kind: 'image' as const, url: image.url }))} startIndex={gallery} onClose={() => setGallery(null)} />
      )}
      {editing && categories.data && <ListingFormSheet listing={data} categories={categories.data} onClose={() => setEditing(false)} />}
    </div>
  )
}

/** Flecha sobre la foto. Con mouse aparece al pasar por encima; en touch siempre se ve. */
function PhotoArrow({ side, onClick }: { side: 'left' | 'right'; onClick: () => void }) {
  const Icon = side === 'left' ? ChevronLeft : ChevronRight
  return (
    <button type="button" onClick={onClick} aria-label={side === 'left' ? 'Foto anterior' : 'Foto siguiente'}
      className={cn('pressable absolute top-1/2 -mt-5 grid size-10 place-items-center rounded-full bg-white/90 text-slate-800 shadow-md shadow-slate-900/10 backdrop-blur-sm',
        'transition-[opacity,transform,background-color] duration-200 hover:bg-white focus-visible:opacity-100',
        '[@media(hover:hover)_and_(pointer:fine)]:opacity-0 [@media(hover:hover)_and_(pointer:fine)]:group-hover:opacity-100',
        side === 'left' ? 'left-3' : 'right-3')}>
      <Icon className="size-5" aria-hidden />
    </button>
  )
}
