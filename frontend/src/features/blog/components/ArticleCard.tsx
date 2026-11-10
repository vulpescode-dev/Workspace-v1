import { MessageCircle } from 'lucide-react'
import { Link } from 'react-router'

import { Card } from '@/components/ui/Card'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { cn } from '@/lib/cn'
import { formatFullDateTime, formatLongDate } from '@/lib/format'

import type { Article } from '../api/blog.api'
import { ArticleCover } from './ArticleCover'
import { ArticleStatusBadge } from './ArticleStatusBadge'

/**
 * Tarjeta de noticia: portada, categoría, título, resumen y autor con fecha. `featured` = la más reciente,
 * a todo el ancho con la portada al lado en pantallas grandes.
 */
export function ArticleCard({ article, featured = false }: { article: Article; featured?: boolean }) {
  const date = article.published_at ?? article.updated_at
  return (
    <Card className="group overflow-hidden transition-shadow duration-200 hover:shadow-md">
      <Link to={`/blog/${article.id}`} className={cn('flex h-full flex-col', featured && 'md:flex-row')}>
        <ArticleCover url={article.cover_url} className={cn('shrink-0', featured && 'md:aspect-auto md:w-3/5')} />
        <div className={cn('flex flex-1 flex-col gap-2 p-4', featured && 'md:justify-center md:p-8')}>
          <div className="flex flex-wrap items-center gap-2">
            {article.category && <span className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-semibold text-brand-700">{article.category.name}</span>}
            <ArticleStatusBadge article={article} />
          </div>
          <h2 className={cn('font-bold text-slate-900 transition-colors duration-150 group-hover:text-brand-700', featured ? 'text-2xl md:text-3xl' : 'line-clamp-2 text-lg')}>{article.title}</h2>
          {article.excerpt && <p className={cn('text-sm text-slate-600', featured ? 'line-clamp-4 md:text-base' : 'line-clamp-3')}>{article.excerpt}</p>}
          <div className="mt-auto flex items-center gap-2.5 pt-2 text-xs text-slate-500">
            <UserAvatar user={article.author} size="sm" />
            <span className="grid min-w-0">
              <span className="truncate font-semibold text-slate-700">{article.author.name}</span>
              <time dateTime={date} title={formatFullDateTime(date)} className="truncate">{formatLongDate(date)}</time>
            </span>
            {article.comments_count > 0 && (
              <span className="ml-auto flex shrink-0 items-center gap-1"><MessageCircle className="size-3.5" aria-hidden />{article.comments_count}</span>
            )}
          </div>
        </div>
      </Link>
    </Card>
  )
}
