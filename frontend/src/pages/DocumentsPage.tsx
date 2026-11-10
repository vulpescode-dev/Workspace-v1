import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { FolderOpen, Search, Upload } from 'lucide-react'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router'

import { EmptyState } from '@/components/feedback/EmptyState'
import { ListSkeleton } from '@/components/feedback/ListSkeleton'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Tabs } from '@/components/ui/Tabs'
import { documentsApi, documentsKeys, VISIBILITY_LABELS, type DocumentItem } from '@/features/documents/api/documents.api'
import { FileTypeIcon } from '@/features/documents/components/FileTypeIcon'
import { formatSize, VISIBILITY_ICONS } from '@/features/documents/utils'
import { UploadDocumentSheet } from '@/features/documents/components/UploadDocumentSheet'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { cn } from '@/lib/cn'
import { formatRelative } from '@/lib/format'

const SCOPES = [
  { value: 'all', label: 'Todos' },
  { value: 'mine', label: 'Míos' },
  { value: 'shared', label: 'Compartidos conmigo' },
] as const

/** /documents — biblioteca: Todos · Míos · Compartidos, búsqueda y categorías (todo en la URL). */
export function DocumentsPage() {
  useDocumentTitle('Documentos')
  const [params, setParams] = useSearchParams()
  const [text, setText] = useState(params.get('q') ?? '')
  const q = useDebouncedValue(text.trim(), 300)
  const scope = (params.get('scope') as 'mine' | 'shared' | null) ?? undefined
  const category = Number(params.get('category')) || undefined
  const filters = { scope, category, q }
  const [uploading, setUploading] = useState(false)

  const me = useQuery({ queryKey: documentsKeys.me(), queryFn: documentsApi.me, staleTime: 5 * 60_000 })
  const categories = useQuery({ queryKey: documentsKeys.categories(), queryFn: documentsApi.categories, staleTime: 10 * 60_000 })
  const list = useInfiniteQuery({
    queryKey: documentsKeys.list(filters),
    queryFn: ({ pageParam }) => documentsApi.list(filters, pageParam),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page < last.total_pages ? last.page + 1 : undefined),
    placeholderData: (previous) => previous,
  })

  function update(next: Record<string, string>) {
    const merged = new URLSearchParams(params)
    Object.entries(next).forEach(([key, value]) => (value ? merged.set(key, value) : merged.delete(key)))
    setParams(merged, { replace: true })
  }

  const items = list.data?.pages.flatMap((page) => page.results) ?? []

  return (
    <>
      <PageHeader
        title="Documentos"
        description="Políticas, formatos y recursos de la empresa, siempre en su versión vigente."
        actions={me.data?.can_create && <Button onClick={() => setUploading(true)}><Upload className="size-4" aria-hidden /> Subir documento</Button>}
      />
      <Tabs label="Qué documentos ver" options={[...SCOPES]} value={scope ?? 'all'} onChange={(value) => update({ scope: value === 'all' ? '' : value })} className="mb-4" />

      <Card className="mb-4 grid gap-3 p-3">
        <label className="relative">
          <span className="sr-only">Buscar documentos</span>
          <Search className="pointer-events-none absolute top-1/2 left-3.5 size-5 -translate-y-1/2 text-slate-400" aria-hidden />
          <input
            type="search"
            value={text}
            onChange={(event) => { setText(event.target.value); update({ q: event.target.value.trim() }) }}
            placeholder="Buscar por título o descripción"
            className="h-11 w-full rounded-xl border border-slate-200 pr-3 pl-11 text-base placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm"
          />
        </label>
        {(categories.data?.length ?? 0) > 0 && (
          <div className="flex gap-2 overflow-x-auto [scrollbar-width:none]" role="group" aria-label="Categorías">
            {[{ id: 0, name: 'Todas' }, ...categories.data!].map((item) => {
              const active = (category ?? 0) === item.id
              return (
                <button
                  key={item.id}
                  type="button"
                  aria-pressed={active}
                  onClick={() => update({ category: item.id ? String(item.id) : '' })}
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
        <Card className="p-4"><ListSkeleton rows={6} label="Cargando documentos" /></Card>
      ) : list.isError ? (
        <Card><EmptyState icon={FolderOpen} title="No se pudieron cargar los documentos" action={<Button variant="outline" onClick={() => void list.refetch()}>Reintentar</Button>} /></Card>
      ) : items.length === 0 ? (
        <Card>
          <EmptyState
            icon={FolderOpen}
            title={q || category ? 'Ningún documento coincide' : 'Todavía no hay documentos'}
            description={q || category ? 'Prueba con otras palabras o con otra categoría.' : me.data?.can_create ? 'Sube el primero con «Subir documento».' : 'Cuando se compartan documentos contigo aparecerán aquí.'}
          />
        </Card>
      ) : (
        <Card className={cn('divide-y divide-slate-100 overflow-hidden', list.isPlaceholderData && 'opacity-60')}>
          <ul>{items.map((item) => <DocumentRow key={item.id} item={item} />)}</ul>
        </Card>
      )}
      {list.hasNextPage && (
        <Button variant="outline" className="mx-auto mt-4 flex" loading={list.isFetchingNextPage} onClick={() => void list.fetchNextPage()}>Ver más documentos</Button>
      )}

      {uploading && <UploadDocumentSheet categories={categories.data ?? []} onClose={() => setUploading(false)} />}
    </>
  )
}

function DocumentRow({ item }: { item: DocumentItem }) {
  const version = item.current_version
  const VisibilityIcon = VISIBILITY_ICONS[item.visibility]
  return (
    <li>
      <Link to={`/documents/${item.id}`} className="flex items-center gap-3 px-4 py-3.5 transition-colors duration-150 hover:bg-slate-50">
        <FileTypeIcon contentType={version?.content_type} name={version?.name} />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-slate-900">{item.title}</p>
          <p className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-slate-500">
            <span className="rounded-full bg-slate-100 px-2 py-0.5 font-medium text-slate-600">{item.category.name}</span>
            <span className="truncate">{item.owner.name}</span>
            <span aria-hidden>·</span>
            <span>{formatRelative(item.updated_at)}</span>
          </p>
        </div>
        <div className="hidden shrink-0 items-center gap-3 text-xs text-slate-500 sm:flex">
          {version && <span className="rounded-md bg-brand-50 px-1.5 py-0.5 font-semibold text-brand-700">v{version.number}</span>}
          {version && <span className="w-14 text-right tabular-nums">{formatSize(version.size)}</span>}
          <VisibilityIcon className="size-4" aria-label={VISIBILITY_LABELS[item.visibility]} />
        </div>
      </Link>
    </li>
  )
}
