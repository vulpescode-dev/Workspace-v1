import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { Search, SearchX, X } from 'lucide-react'
import { useState } from 'react'
import { useSearchParams } from 'react-router'

import { EmptyState } from '@/components/feedback/EmptyState'
import { SkeletonGroup } from '@/components/feedback/Skeleton'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'

import { peopleApi, peopleKeys } from '../api/people.api'
import { PersonCard, PersonCardSkeleton } from './PersonCard'

/**
 * Directorio: buscador (nombre, correo, cargo o área) y filtro por área, en la URL (`?q=`, `?department=`)
 * para poder compartir la búsqueda. 25 por página con «Ver más». Cuadrícula de 1 a 3 columnas.
 */
export function PeopleDirectory() {
  const [params, setParams] = useSearchParams()
  const [text, setText] = useState(params.get('q') ?? '')
  const search = useDebouncedValue(text.trim(), 300)
  const department = Number(params.get('department')) || undefined
  const filters = { search, department }

  const departments = useQuery({ queryKey: peopleKeys.departments(), queryFn: peopleApi.departments, staleTime: 10 * 60_000 })
  const list = useInfiniteQuery({
    queryKey: peopleKeys.directory(filters),
    queryFn: ({ pageParam }) => peopleApi.directory(filters, pageParam),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page < last.total_pages ? last.page + 1 : undefined),
    placeholderData: (previous) => previous,   // al escribir no parpadea: se ven los resultados anteriores
  })

  function update(next: { q?: string; department?: string }) {
    const merged = new URLSearchParams(params)
    for (const [key, value] of Object.entries(next)) {
      if (value) merged.set(key, value)
      else merged.delete(key)
    }
    setParams(merged, { replace: true })
  }

  const people = list.data?.pages.flatMap((page) => page.results) ?? []
  const total = list.data?.pages[0]?.count ?? 0
  const filtering = Boolean(search || department)

  return (
    <div className="grid gap-4">
      <Card className="flex flex-col gap-3 p-3 sm:flex-row sm:items-center">
        <label className="relative flex-1">
          <span className="sr-only">Buscar personas</span>
          <Search className="pointer-events-none absolute top-1/2 left-3.5 size-5 -translate-y-1/2 text-slate-400" aria-hidden />
          <input
            type="search"
            value={text}
            onChange={(event) => {
              setText(event.target.value)
              update({ q: event.target.value.trim() })
            }}
            placeholder="Nombre, correo, cargo o área"
            className="h-11 w-full rounded-xl border border-slate-200 bg-surface pr-10 pl-11 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm [&::-webkit-search-cancel-button]:hidden"
          />
          {text && (
            <button
              type="button"
              onClick={() => {
                setText('')
                update({ q: '' })
              }}
              aria-label="Borrar búsqueda"
              className="absolute top-1/2 right-2 grid size-8 -translate-y-1/2 place-items-center rounded-lg text-slate-400 hover:text-slate-600"
            >
              <X className="size-4" aria-hidden />
            </button>
          )}
        </label>
        <select
          value={department ?? ''}
          onChange={(event) => update({ department: event.target.value })}
          aria-label="Filtrar por área"
          className="h-11 rounded-xl border border-slate-200 bg-surface px-3 text-base text-slate-700 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:w-56 sm:text-sm"
        >
          <option value="">Todas las áreas</option>
          {departments.data?.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
      </Card>

      {!list.isPending && !list.isError && (
        <p className="px-1 text-sm text-slate-500" aria-live="polite">
          {total === 1 ? '1 persona' : `${total} personas`}
          {filtering && (total === 1 ? ' encontrada' : ' encontradas')}
        </p>
      )}

      {list.isPending ? (
        <SkeletonGroup label="Cargando personas" className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }, (_, index) => <PersonCardSkeleton key={index} />)}
        </SkeletonGroup>
      ) : list.isError ? (
        <Card>
          <EmptyState icon={SearchX} title="No se pudo cargar el directorio" action={<Button variant="outline" onClick={() => void list.refetch()}>Reintentar</Button>} />
        </Card>
      ) : people.length === 0 ? (
        <Card>
          <EmptyState icon={SearchX} title="Nadie coincide con tu búsqueda" description="Prueba con otro nombre, cargo o área." />
        </Card>
      ) : (
        <ul className={`grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 ${list.isPlaceholderData ? 'opacity-60' : ''}`}>
          {people.map((person) => (
            <li key={person.id} className="min-w-0">
              <PersonCard person={person} />
            </li>
          ))}
        </ul>
      )}

      {list.hasNextPage && (
        <Button variant="outline" className="mx-auto" loading={list.isFetchingNextPage} onClick={() => void list.fetchNextPage()}>
          Ver más personas
        </Button>
      )}
    </div>
  )
}
