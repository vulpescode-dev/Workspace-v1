import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, BarChart3, Download, Lock } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router'
import { toast } from 'sonner'

import { useCan } from '@/features/accounts/hooks/useCan'
import { EmptyState } from '@/components/feedback/EmptyState'
import { Skeleton } from '@/components/feedback/Skeleton'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { formsApi, formsKeys } from '@/features/forms/api/forms.api'
import { FormTabs } from '@/features/forms/components/FormTabs'
import { QuestionResults } from '@/features/forms/components/QuestionResults'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { getErrorMessage } from '@/lib/api/errors'
import { formatFullDateTime, formatRelative } from '@/lib/format'
import { downloadProtected } from '@/lib/media/download'

/** /forms/:uuid/results — resumen por pregunta y descarga en CSV (abre en Excel). Quien lo creó o quien tenga permiso de ver todos. */
export function FormResultsPage() {
  const uuid = useParams().formId ?? ''
  const form = useQuery({ queryKey: formsKeys.detail(uuid), queryFn: () => formsApi.get(uuid) })
  const can = useCan()
  // Resultados: quien lo creó, o quien tenga permiso de ver todos. CSV ajeno: además «forms.submissions.export».
  const canSee = Boolean(form.data?.is_mine) || can('forms.forms.view.all') || can('forms.submissions.view.all')
  const canExport = Boolean(form.data?.is_mine) || can('forms.submissions.export')
  const results = useQuery({ queryKey: formsKeys.results(uuid), queryFn: () => formsApi.results(uuid), enabled: Boolean(form.data) && canSee, refetchInterval: 60_000 })
  const [downloading, setDownloading] = useState(false)
  useDocumentTitle(form.data ? `Respuestas: ${form.data.title}` : 'Respuestas')

  async function download() {
    setDownloading(true)
    try { await downloadProtected(formsApi.csvUrl(uuid), `${form.data?.title ?? 'formulario'} - respuestas.csv`) } catch (error) { toast.error(getErrorMessage(error, 'No se pudo descargar.')) } finally { setDownloading(false) }
  }

  const back = (
    <Link to="/forms?view=mine" className="inline-flex w-fit items-center gap-2 rounded-lg text-sm font-semibold text-slate-500 hover:text-slate-800">
      <ArrowLeft className="size-4" aria-hidden /> Mis formularios
    </Link>
  )
  if (form.isPending || (canSee && results.isPending)) {
    return <div className="grid gap-4">{back}<Card className="grid gap-3 p-6"><Skeleton className="h-8 w-1/3" /><Skeleton className="h-4 w-1/2" /></Card><Card className="grid gap-3 p-6"><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-4/5" /><Skeleton className="h-4 w-3/5" /></Card></div>
  }
  if (form.isError || !canSee || results.isError) {
    return <div className="grid gap-4">{back}<Card><EmptyState icon={Lock} title={form.data && !canSee ? 'Solo quien creó el formulario ve sus respuestas' : 'No se pudieron cargar las respuestas'} /></Card></div>
  }

  const data = results.data!
  return (
    <div className="grid gap-4">
      {back}
      <FormTabs edit={form.data.is_mine || can('forms.forms.update.all')} uuid={uuid} count={data.submissions_count} />
      <Card className="flex flex-wrap items-center gap-4 p-5">
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-lg font-bold text-slate-900">{form.data.title}</h1>
          <p className="mt-1 text-sm text-slate-500">
            <span className="text-2xl font-bold text-slate-900 tabular-nums">{data.submissions_count}</span> {data.submissions_count === 1 ? 'respuesta' : 'respuestas'}
            {data.last_submitted_at && <> · la última <time title={formatFullDateTime(data.last_submitted_at)}>{formatRelative(data.last_submitted_at)}</time></>}
          </p>
        </div>
        {canExport && <Button variant="outline" disabled={!data.submissions_count} loading={downloading} onClick={() => void download()}><Download className="size-4" aria-hidden /> Descargar CSV</Button>}
      </Card>
      {data.submissions_count === 0 ? (
        <Card><EmptyState icon={BarChart3} title="Aún no hay respuestas" description={form.data.status === 'draft' ? 'Publica el formulario desde «Preguntas» para empezar a recibirlas.' : 'Comparte el enlace para que la gente responda.'} /></Card>
      ) : (
        data.questions.map((result) => <QuestionResults key={result.id} result={result} />)
      )}
    </div>
  )
}
