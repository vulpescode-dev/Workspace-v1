import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { ArrowLeft, CheckCircle2, Clock, FileX, Lock } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router'
import { toast } from 'sonner'

import { useCan } from '@/features/accounts/hooks/useCan'
import { EmptyState } from '@/components/feedback/EmptyState'
import { Skeleton } from '@/components/feedback/Skeleton'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { formsApi, formsKeys, type AnswerInput, type FormDetail } from '@/features/forms/api/forms.api'
import { FormTabs } from '@/features/forms/components/FormTabs'
import { QuestionField } from '@/features/forms/components/QuestionField'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { getErrorMessage } from '@/lib/api/errors'
import { formatFullDateTime } from '@/lib/format'

/** /forms/:uuid — responder un formulario (para quien lo creó es la «Vista previa»; también puede responderlo). */
export function FormPage() {
  const can = useCan()
  const uuid = useParams().formId ?? ''
  const form = useQuery({ queryKey: formsKeys.detail(uuid), queryFn: () => formsApi.get(uuid) })
  useDocumentTitle(form.data?.title ?? 'Formulario')

  const back = (
    <Link to="/forms" className="inline-flex w-fit items-center gap-2 rounded-lg text-sm font-semibold text-slate-500 hover:text-slate-800">
      <ArrowLeft className="size-4" aria-hidden /> Formularios
    </Link>
  )

  if (form.isPending) {
    return <div className="grid gap-4">{back}<Card className="grid gap-3 p-6"><Skeleton className="h-8 w-2/3" /><Skeleton className="h-4 w-full" /></Card><Card className="grid gap-3 p-6"><Skeleton className="h-5 w-1/2" /><Skeleton className="h-10" /></Card></div>
  }
  if (form.isError) {
    const gone = isAxiosError(form.error) && form.error.response?.status === 404
    return (
      <div className="grid gap-4">
        {back}
        <Card><EmptyState icon={FileX} title={gone ? 'Este formulario no está disponible' : 'No se pudo cargar el formulario'} description={gone ? 'Puede que se haya eliminado o que aún no se publique.' : undefined}
          action={gone ? undefined : <Button variant="outline" onClick={() => void form.refetch()}>Reintentar</Button>} /></Card>
      </div>
    )
  }

  return (
    <div className="grid gap-4">
      {back}
      {/* Pestañas: el dueño todas; los demás, las que sus permisos abren (editar / ver resultados). */}
      {(() => {
        const canEdit = form.data.is_mine || can('forms.forms.update.all')
        const canResults = form.data.is_mine || can('forms.forms.view.all') || can('forms.submissions.view.all')
        return (canEdit || canResults) && <FormTabs uuid={uuid} count={form.data.submissions_count} edit={canEdit} results={canResults} />
      })()}
      <FormBody form={form.data} />
    </div>
  )
}

function FormBody({ form }: { form: FormDetail }) {
  const queryClient = useQueryClient()
  const [values, setValues] = useState<Record<number, AnswerInput>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [sent, setSent] = useState(false)
  const alreadySent = form.submitted && form.one_submission_per_user

  const submit = useMutation({
    mutationFn: () => formsApi.submit(form.uuid, form.questions.map((question) => ({ ...values[question.id!], question: question.id! }))),
    onSuccess: () => {
      setSent(true)
      setValues({})
      setErrors({})
      void queryClient.invalidateQueries({ queryKey: formsKeys.lists() })
      void queryClient.invalidateQueries({ queryKey: formsKeys.results(form.uuid) })
      window.scrollTo({ top: 0, behavior: 'smooth' })
    },
    onError: (error) => {
      const byQuestion = isAxiosError(error) && (error.response?.data as { answers?: unknown })?.answers
      if (byQuestion && typeof byQuestion === 'object') {
        setErrors(byQuestion as Record<string, string>)
        const first = form.questions.find((question) => (byQuestion as Record<string, string>)[String(question.id)])
        document.getElementById(`question-${first?.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
        toast.error('Revisa las preguntas marcadas.')
      } else {
        toast.error(getErrorMessage(error, 'No se pudo enviar.'))
      }
    },
  })

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!submit.isPending) submit.mutate()
  }

  const header = (
    <Card className="overflow-hidden">
      <div className="h-2 bg-brand-500" aria-hidden />
      <div className="grid gap-3 p-6">
        <h1 className="text-2xl font-bold break-words text-slate-900 sm:text-3xl">{form.title}</h1>
        {form.description && <p className="text-sm break-words whitespace-pre-line text-slate-600">{form.description}</p>}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-slate-100 pt-3 text-xs text-slate-500">
          <span className="flex items-center gap-2"><UserAvatar user={form.owner} size="sm" /> {form.owner.name}</span>
          {form.closes_at && form.accepting && <span className="flex items-center gap-1.5"><Clock className="size-3.5" aria-hidden /> Cierra el {formatFullDateTime(form.closes_at)}</span>}
          {form.questions.some((question) => question.is_required) && <span><span className="text-red-500">*</span> Obligatoria</span>}
        </div>
      </div>
    </Card>
  )

  if (sent || (alreadySent && !form.is_mine)) {
    return (
      <>
        {header}
        <Card>
          <EmptyState icon={CheckCircle2} title={sent ? '¡Gracias! Tu respuesta se envió.' : 'Ya respondiste este formulario'}
            description={form.one_submission_per_user ? 'Solo se permite una respuesta por persona.' : undefined}
            action={!form.one_submission_per_user && form.accepting ? <Button variant="outline" onClick={() => setSent(false)}>Enviar otra respuesta</Button> : <Button variant="outline" onClick={() => history.back()}>Volver</Button>} />
        </Card>
      </>
    )
  }

  return (
    <>
      {header}
      {form.status === 'draft' && <Alert tone="info">Es un borrador: solo tú lo ves. Ábrelo desde «Preguntas» para recibir respuestas.</Alert>}
      {!form.accepting && form.status !== 'draft' && (
        <Card><EmptyState icon={Lock} title="Este formulario ya no recibe respuestas" description="Si crees que es un error, contacta a quien lo publicó." /></Card>
      )}
      {form.accepting && alreadySent && form.is_mine && <Alert tone="info">Ya lo respondiste: puedes ver la vista previa, pero no enviar otra respuesta.</Alert>}
      {form.questions.length === 0 ? (
        <Card><EmptyState icon={FileX} title="Este formulario aún no tiene preguntas" /></Card>
      ) : (
        <form onSubmit={onSubmit} className="grid gap-4" noValidate>
          {form.questions.map((question) => (
            <div key={question.id} id={`question-${question.id}`} className="scroll-mt-24">
              <QuestionField
                question={question}
                value={values[question.id!] ?? { question: question.id! }}
                error={errors[String(question.id)]}
                onChange={(value) => {
                  setValues((current) => ({ ...current, [question.id!]: value }))
                  if (errors[String(question.id)]) setErrors((current) => Object.fromEntries(Object.entries(current).filter(([key]) => key !== String(question.id))))
                }}
              />
            </div>
          ))}
          {form.accepting && !alreadySent && (
            <div className="flex items-center justify-between gap-3">
              <Button variant="ghost" onClick={() => { setValues({}); setErrors({}) }}>Borrar respuestas</Button>
              <Button type="submit" loading={submit.isPending}>Enviar</Button>
            </div>
          )}
        </form>
      )}
    </>
  )
}
