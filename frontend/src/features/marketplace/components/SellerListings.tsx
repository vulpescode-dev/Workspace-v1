import { useQuery } from '@tanstack/react-query'
import { ArrowRight } from 'lucide-react'
import { useMemo } from 'react'
import { Link } from 'react-router'

import type { UserSummary } from '@/features/accounts/types'

import { marketplaceApi, marketplaceKeys, type Listing } from '../api/marketplace.api'
import { ListingCard } from './ListingCard'

const SHOWN = 4

/** Baraja sin tocar el arreglo original (Fisher–Yates). */
function shuffle<T>(items: T[]): T[] {
  const copy = [...items]
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy
}

/**
 * «Más de <vendedor>»: hasta 4 anuncios disponibles del mismo vendedor, en orden aleatorio y sin el que
 * se está viendo. Usa el filtro `seller` que ya tiene la API. Si no vende nada más, no se muestra.
 */
export function SellerListings({ seller, excludeId }: { seller: UserSummary; excludeId: number }) {
  const filters = { seller: seller.id, status: 'available' as const }
  const listings = useQuery({ queryKey: marketplaceKeys.list(filters), queryFn: () => marketplaceApi.list(filters, 1), staleTime: 60_000 })

  // Se baraja una vez por anuncio visto, no en cada render (si no, las tarjetas «saltarían»). React Query
  // conserva la misma referencia de `data` mientras no cambie el contenido.
  const results = listings.data?.results
  const picks = useMemo<Listing[]>(
    () => shuffle((results ?? []).filter((item) => item.id !== excludeId)).slice(0, SHOWN),
    [results, excludeId],
  )

  if (!picks.length) return null
  const firstName = seller.name.split(' ')[0]

  return (
    <section aria-labelledby="seller-more" className="grid gap-3">
      <div className="flex items-end justify-between gap-3">
        <div>
          <h2 id="seller-more" className="text-lg font-bold text-slate-900">Más de {firstName}</h2>
          <p className="text-sm text-slate-500">Otros artículos que vende {seller.name}.</p>
        </div>
        <Link to={`/profile/${seller.id}`}
          className="group inline-flex shrink-0 items-center gap-1 rounded-lg text-sm font-semibold text-brand-600 hover:text-brand-700">
          Ver perfil <ArrowRight className="size-4 transition-transform duration-200 ease-(--ease-out) group-hover:translate-x-0.5" aria-hidden />
        </Link>
      </div>
      <ul className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3">
        {picks.map((item, index) => (
          <li key={item.id} className="animate-enter" style={{ animationDelay: `${index * 50}ms` }}>
            <ListingCard listing={item} />
          </li>
        ))}
      </ul>
    </section>
  )
}
