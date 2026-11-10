import { Images } from 'lucide-react'
import { Link } from 'react-router'

import { Card } from '@/components/ui/Card'
import { cn } from '@/lib/cn'
import { formatRelative } from '@/lib/format'

import { formatPrice, type Listing } from '../api/marketplace.api'
import { ListingPhoto } from './ListingPhoto'

/** Tarjeta de anuncio: foto cuadrada, precio grande, título y quién lo vende. Vendido = foto apagada con etiqueta. */
export function ListingCard({ listing }: { listing: Listing }) {
  const sold = listing.status === 'sold'
  return (
    <Card className="group overflow-hidden transition-shadow duration-200 hover:shadow-md">
      <Link to={`/marketplace/${listing.id}`} className="flex h-full flex-col">
        <div className="relative">
          <ListingPhoto url={listing.images[0]?.url} className={cn('aspect-square transition-[filter] duration-200', sold && 'grayscale-[60%]')} />
          {sold && <span className="absolute top-2 left-2 rounded-full bg-slate-900/80 px-2.5 py-1 text-xs font-bold text-white">Vendido</span>}
          {listing.images.length > 1 && (
            <span className="absolute right-2 bottom-2 flex items-center gap-1 rounded-full bg-slate-900/60 px-2 py-0.5 text-xs font-semibold text-white tabular-nums">
              <Images className="size-3.5" aria-hidden /> {listing.images.length}
            </span>
          )}
        </div>
        <div className="flex flex-1 flex-col gap-0.5 p-3">
          <p className={cn('text-lg font-bold tabular-nums', sold ? 'text-slate-400 line-through' : 'text-slate-900')}>{formatPrice(listing.price)}</p>
          <p className="line-clamp-2 text-sm font-medium text-slate-700 transition-colors duration-150 group-hover:text-brand-700">{listing.title}</p>
          <p className="mt-auto truncate pt-1 text-xs text-slate-500">{listing.seller.name} · {formatRelative(listing.created_at)}</p>
        </div>
      </Link>
    </Card>
  )
}
