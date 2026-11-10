import type { UserSummary } from '@/features/accounts/types'
import { api } from '@/lib/api/client'
import type { Paginated } from '@/types/api'

export interface ListingCategory { id: number; name: string; slug: string }
export interface ListingImage {
  id: number
  /** Vista autorizada de la API (nunca /media/). */
  url: string
  width: number | null
  height: number | null
}

/** Anuncio (`GET /api/marketplace/listings/`). `price` llega como texto («1500.00») o `null` = «A tratar». */
export interface Listing {
  id: number
  seller: UserSummary
  category: ListingCategory | null
  title: string
  description: string
  price: string | null
  status: 'available' | 'sold'
  sold_at: string | null
  images: ListingImage[]
  created_at: string
  updated_at: string
  is_mine: boolean
}

export interface ListingFilters { q?: string; category?: string; status?: 'available' | 'sold'; seller?: number }

export const MAX_LISTING_IMAGES = 10

export const marketplaceApi = {
  categories: () => api.get<ListingCategory[]>('/marketplace/categories/').then(({ data }) => data),
  list: ({ q, category, status, seller }: ListingFilters, page: number) =>
    api.get<Paginated<Listing>>('/marketplace/listings/', { params: { q: q || undefined, category: category || undefined, status, seller, page } }).then(({ data }) => data),
  get: (id: number) => api.get<Listing>(`/marketplace/listings/${id}/`).then(({ data }) => data),
  /** Multipart: `title`, `description`, `price`, `category` y `files` (WebP, repetido). */
  create: (form: FormData) => api.post<Listing>('/marketplace/listings/', form).then(({ data }) => data),
  /** Solo lo que cambió; `status` marca vendido/disponible. */
  update: (id: number, changes: Partial<{ title: string; description: string; price: string | null; category: number | null; status: Listing['status'] }>) =>
    api.patch<Listing>(`/marketplace/listings/${id}/`, changes).then(({ data }) => data),
  remove: (id: number) => api.delete(`/marketplace/listings/${id}/`),
  addImages: (id: number, files: File[]) => {
    const form = new FormData()
    files.forEach((file) => form.append('files', file))
    return api.post<Listing>(`/marketplace/listings/${id}/images/`, form).then(({ data }) => data)
  },
  removeImage: (imageId: number) => api.delete(`/marketplace/images/${imageId}/`),
}

export const marketplaceKeys = {
  all: ['marketplace'] as const,
  categories: () => [...marketplaceKeys.all, 'categories'] as const,
  lists: () => [...marketplaceKeys.all, 'list'] as const,
  list: (filters: ListingFilters) => [...marketplaceKeys.lists(), filters] as const,
  detail: (id: number) => [...marketplaceKeys.all, 'detail', id] as const,
}

const wholePrice = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 })
const centsPrice = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 2 })

/** «$1,500», «$249.50» o «A tratar». Los centavos solo se muestran si los hay. */
export function formatPrice(price: string | null) {
  if (price === null || price === '') return 'A tratar'
  const value = Number(price)
  return (Number.isInteger(value) ? wholePrice : centsPrice).format(value)
}
