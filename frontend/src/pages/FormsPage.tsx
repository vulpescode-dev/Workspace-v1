import { useInfiniteQuery, useMutation, useQuery } from '@tanstack/react-query'
import { CheckCircle2, ClipboardList, Clock, Plus, Search } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { toast } from 'sonner'

import { EmptyState } from '@/components/feedback/EmptyState'
import { ListSkeleton } from '@/components/feedback/ListSkeleton'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Tabs } from '@/components/ui/Tabs'
import { formsApi, formsKeys, STATUS_LABELS, type FormScope, type FormSummary } from '@/features/forms/api/forms.api'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { getErrorMessage } from '@/lib/api/errors'
import { cn } from '@/lib/cn'
import { formatFullDateTime, formatLongDate, formatRelative } from '@/lib/format'

/** /forms — Por responder · Todos · Mis formularios (si puede crear). Búsqueda y pestaña en la URL. */
export function FormsPage() {
  useDocumentTitle('Formularios')
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const [text, setText] = useState(params.get('q') ?? '')
  const q = useDebouncedValue(text.trim(), 300)
  const view = params.get('view') ?? 'pending'
  const scope: FormScope | undefined = view === 'all' ? undefined : (view as FormScope)

  const me = useQuery({ queryKey: formsKeys.me(), queryFn: formsApi.me, staleTime: 5 * 60_000 })
  const list = useInfiniteQuery({
    queryKey: formsKeys.list(scope, q),
    queryFn: ({ pageParam }) => formsApi.list(scope, q, pageParam),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page < last.total_pages ? last.page + 1 : undefined),
    placeholderData: (previous) => previous,
  })
  const create = useMutation({
    mutationFn: () => formsApi.create('Formulario sin título'),
    onSuccess: (form) => navigate(`/forms/${form.uuid}/edit`),
    onError: (error) => toast.error(getErrorMessage(error, 'No se pudo crear el formulario.')),
  })

  function update(next: Record<string, string>) {
    const merged = new URLSearchParams(params)
    Object.entries(next).forEach(([key, value]) => (value ? merged.set(key, value) : merged.delete(key)))
    setParams(merged, { replace: true })
  }

  const canCreate = me.data?.can_create ?? false
  const items = list.data?.pages.flatMap((page) => page.results) ?? []
  const views = [{ value: 'pending', label: 'Por responder' }, { value: 'all', label: 'Todos' }, ...(canCreate ? [{ value: 'mine', label: 'Mis formularios' }] : [])]

  return (
    <>
      <PageHeader
        title="Formularios"
        description="Encuestas, inscripciones y solicitudes de la empresa."
        actions={canCreate && <Button loading={create.isPending} onClick={() => create.mutate()}><Plus className="size-4" aria-hidden /> Nuevo formulario</Button>}
      />
      <Tabs label="Qué formularios ver" options={views} value={view} onChange={(value) => update({ view: value === 'pending' ? '' : value })} className="mb-4" />
      <Card className="mb-4 p-3">
        <label className="relative block">
          <span className="sr-only">Buscar formularios</span>
          <Search className="pointer-events-none absolute top-1/2 left-3.5 size-5 -translate-y-1/2 text-slate-400" aria-hidden />
          <input type="search" value={text} onChange={(event) => { setText(event.target.value); update({ q: event.target.value.trim() }) }} placeholder="Buscar por título"
            className="h-11 w-full rounded-xl border border-slate-200 pr-3 pl-11 text-base placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm" />
        </label>
      </Card>

      {list.isPending ? (
        <Card className="p-4"><ListSkeleton rows={5} label="Cargando formularios" /></Card>
      ) : list.isError ? (
        <Card><EmptyState icon={ClipboardList} title="No se pudieron cargar los formularios" action={<Button variant="outline" onClick={() => void list.refetch()}>Reintentar</Button>} /></Card>
      ) : items.length === 0 ? (
        <Card>
          <EmptyState
            icon={view === 'pending' && !q ? CheckCircle2 : ClipboardList}
            title={q ? 'Ningún formulario coincide' : view === 'pending' ? '¡Estás al día!' : view === 'mine' ? 'Aún no creas formularios' : 'Todavía no hay formularios'}
            description={q ? 'Prueba con otras palabras.' : view === 'pending' ? 'No tienes formularios pendientes por responder.' : view === 'mine' ? 'Crea una encuesta o un registro con «Nuevo formulario».' : undefined}
          />
        </Card>
      ) : (
        <Card className={cn('overflow-hidden transition-opacity duration-150', list.isPlaceholderData && 'opacity-60')}>
          <ul className="divide-y divide-slate-100">{items.map((form) => <FormRow key={form.uuid} form={form} />)}</ul>
        </Card>
      )}
      {list.hasNextPage && <Button variant="outline" className="mx-auto mt-4 flex" loading={list.isFetchingNextPage} onClick={() => void list.fetchNextPage()}>Ver más</Button>}
    </>
  )
}

function FormRow({ form }: { form: FormSummary }) {
  const to = form.is_mine ? (form.status === 'draft' ? `/forms/${form.uuid}/edit` : `/forms/${form.uuid}/results`) : `/forms/${form.uuid}`
  return (
    <li>
      <Link to={to} className="flex items-center gap-3 px-4 py-3.5 transition-colors duration-150 hover:bg-slate-50">
        <span className={cn('grid size-11 shrink-0 place-items-center rounded-xl', form.submitted ? 'bg-emerald-50 text-emerald-600' : 'bg-brand-50 text-brand-600')}>
          {form.submitted ? <CheckCircle2 className="size-5" aria-hidden /> : <ClipboardList className="size-5" aria-hidden />}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-slate-900">{form.title}</p>
          <p className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-slate-500">
            {form.is_mine ? (
              <>
                <span className={cn('rounded-full px-2 py-0.5 font-semibold', form.status === 'open' ? 'bg-emerald-50 text-emerald-700' : form.status === 'draft' ? 'bg-amber-50 text-amber-700' : 'bg-slate-100 text-slate-600')}>{STATUS_LABELS[form.status]}</span>
                <span>{form.submissions_count} {form.submissions_count === 1 ? 'respuesta' : 'respuestas'}</span>
              </>
            ) : (
              <span className="truncate">{form.owner.name}</span>
            )}
            <span aria-hidden>·</span>
            {form.submitted ? <span className="font-medium text-emerald-700">Respondido</span>
              : form.accepting && form.closes_at ? <span className="flex items-center gap-1"><Clock className="size-3" aria-hidden /><time title={formatFullDateTime(form.closes_at)}>Cierra: {formatLongDate(form.closes_at)}</time></span>
              : !form.accepting && form.status === 'closed' ? <span>Cerrado</span>
              : <span>{formatRelative(form.created_at)}</span>}
          </p>
        </div>
      </Link>
    </li>
  )
}
