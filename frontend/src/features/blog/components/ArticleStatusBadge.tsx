import { formatFullDateTime } from '@/lib/format'

import type { Article } from '../api/blog.api'

/** «Borrador» o «Programado» (solo los ve quien escribió el artículo). Publicado no lleva etiqueta. */
export function ArticleStatusBadge({ article }: { article: Article }) {
  if (article.status === 'draft') return <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700">Borrador</span>
  if (article.is_scheduled && article.published_at) {
    return <span title={formatFullDateTime(article.published_at)} className="rounded-full bg-violet-50 px-2.5 py-0.5 text-xs font-semibold text-violet-700">Programado</span>
  }
  return null
}
