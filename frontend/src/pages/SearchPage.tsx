import { useQueries } from '@tanstack/react-query'
import { ChevronRight, Search, SearchX } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { Link, useSearchParams } from 'react-router'

import { EmptyState } from '@/components/feedback/EmptyState'
import { Skeleton } from '@/components/feedback/Skeleton'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card } from '@/components/ui/Card'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import type { Section } from '@/features/accounts/access'
import { useSectionAccess } from '@/features/accounts/hooks/useCan'
import { SEARCH_SECTIONS, type SearchHit } from '@/features/search/api/search.api'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { cn } from '@/lib/cn'

const MIN_CHARS = 2

/** Resalta las coincidencias (sin distinguir mayúsculas). */
function highlight(text: string, query: string): ReactNode {
  if (!query) return text
  const lower = text.toLowerCase()
  const needle = query.toLowerCase()
  const parts: ReactNode[] = []
  let from = 0
  for (let at = lower.indexOf(needle); at !== -1; at = lower.indexOf(needle, from)) {
    parts.push(text.slice(from, at), <mark key={at} className="rounded bg-amber-100 px-0.5 text-inherit">{text.slice(at, at + needle.length)}</mark>)
    from = at + needle.length
  }
  parts.push(text.slice(from))
  return parts
}

/**
 * /search — búsqueda general: personas, publicaciones, documentos, noticias, formularios, marketplace y
 * mesa de ayuda. Cada sección muestra sus primeros 5 resultados y «Ver todos» abre la sección con la
 * búsqueda puesta. El texto va en la URL (`?q=`) para poder compartirla o regresar a ella.
 */
export function SearchPage() {
  useDocumentTitle('Buscar')
  const [params, setParams] = useSearchParams()
  const [text, setText] = useState(params.get('q') ?? '')
  const q = useDebouncedValue(text.trim(), 300)
  const active = q.length >= MIN_CHARS
  // Solo se busca en las secciones que puedo abrir (las demás responderían 403).
  const { canSee } = useSectionAccess()
  const sections = SEARCH_SECTIONS.filter((section) => canSee(section.id as Section))

  const results = useQueries({
    queries: sections.map((section) => ({
      queryKey: ['search', section.id, q],
      queryFn: () => section.fetch(q),
      enabled: active,
      staleTime: 30_000,
      placeholderData: (previous: Awaited<ReturnType<typeof section.fetch>> | undefined) => previous,
    })),
  })

  const loading = active && results.some((result) => result.isPending)
  const total = results.reduce((sum, result) => sum + (result.data?.count ?? 0), 0)
  const failed = results.filter((result) => result.isError).length

  return (
    <>
      <PageHeader title="Buscar" description="Personas, publicaciones, documentos, noticias, formularios y más." />
      <Card className="mb-5 p-3">
        <label className="relative block">
          <span className="sr-only">Buscar en Workspace</span>
          <Search className="pointer-events-none absolute top-1/2 left-4 size-5 -translate-y-1/2 text-slate-400" aria-hidden />
          <input
            type="search"
            autoFocus
            value={text}
            onChange={(event) => {
              setText(event.target.value)
              const next = new URLSearchParams(params)
              if (event.target.value.trim()) next.set('q', event.target.value.trim())
              else next.delete('q')
              setParams(next, { replace: true })
            }}
            placeholder="¿Qué buscas?"
            className="h-12 w-full rounded-xl border border-slate-200 pr-3 pl-12 text-base placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none"
          />
        </label>
      </Card>

      {!active ? (
        <Card><EmptyState icon={Search} title="Escribe lo que buscas" description={`Al menos ${MIN_CHARS} letras: un nombre, un documento, un folio de ticket (HD-00042)…`} /></Card>
      ) : !loading && total === 0 && !failed ? (
        <Card><EmptyState icon={SearchX} title={`Nada coincide con «${q}»`} description="Prueba con otras palabras o revisa la ortografía." /></Card>
      ) : (
        <div className="grid gap-4">
          {!loading && <p className="px-1 text-sm text-slate-500">{total} {total === 1 ? 'resultado' : 'resultados'} para «{q}»</p>}
          {sections.map((section, index) => {
            const result = results[index]
            if (result.isPending) return <SectionSkeleton key={section.id} label={section.label} />
            if (result.isError) return <Card key={section.id} className="p-4 text-sm text-slate-500">{section.label}: no se pudo buscar.</Card>
            const data = result.data
            if (!data || data.count === 0) return null
            return (
              <Card key={section.id} className={cn('overflow-hidden transition-opacity duration-150', result.isPlaceholderData && 'opacity-60')}>
                <div className="flex items-center justify-between gap-3 border-b border-slate-100 px-4 py-3">
                  <h2 className="text-sm font-bold text-slate-900">{section.label} <span className="font-medium text-slate-400 tabular-nums">{data.count}</span></h2>
                  {data.count > data.hits.length && (section.all ? (
                    <Link to={section.all(q)} className="flex items-center gap-0.5 text-sm font-semibold text-brand-600 hover:underline">Ver todos <ChevronRight className="size-4" aria-hidden /></Link>
                  ) : (
                    <span className="text-xs text-slate-500">Mostrando {data.hits.length} de {data.count}; afina la búsqueda</span>
                  ))}
                </div>
                <ul className="divide-y divide-slate-100">{data.hits.map((hit) => <HitRow key={hit.key} hit={hit} query={q} />)}</ul>
              </Card>
            )
          })}
        </div>
      )}
    </>
  )
}

function HitRow({ hit, query }: { hit: SearchHit; query: string }) {
  return (
    <li>
      <Link to={hit.to} className="flex items-center gap-3 px-4 py-3 transition-colors duration-150 hover:bg-slate-50">
        {hit.person && <UserAvatar user={hit.person} size="sm" />}
        <span className="min-w-0 flex-1">
          <span className="line-clamp-2 text-sm font-semibold break-words text-slate-900">{highlight(hit.title, query)}</span>
          {hit.subtitle && <span className="block truncate text-xs text-slate-500">{highlight(hit.subtitle, query)}</span>}
        </span>
      </Link>
    </li>
  )
}

function SectionSkeleton({ label }: { label: string }) {
  return (
    <Card className="grid gap-3 p-4" aria-busy aria-label={`Buscando en ${label}`}>
      <Skeleton className="h-4 w-28" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
    </Card>
  )
}
