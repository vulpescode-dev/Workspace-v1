/** Formas compartidas de la API de Django REST Framework. */

/** Lista paginada (`SafePageNumberPagination`, 25 por página). */
export interface Paginated<T> {
  count: number
  page: number
  total_pages: number
  next: string | null
  previous: string | null
  results: T[]
}
