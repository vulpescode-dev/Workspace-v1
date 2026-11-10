import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { ArrowLeft, Check, Copy, FileX, Lock, Plus, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useBlocker, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'

import { useCan } from '@/features/accounts/hooks/useCan'
import { EmptyState } from '@/components/feedback/EmptyState'
import { Skeleton } from '@/components/feedback/Skeleton'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { blankQuestion, formsApi, formsKeys, type FormDetail, type FormStatus, type Question } from '@/features/forms/api/forms.api'
import { FormTabs } from '@/features/forms/components/FormTabs'
import { QuestionEditor } from '@/features/forms/components/QuestionEditor'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { getErrorMessage } from '@/lib/api/errors'
import { cn } from '@/lib/cn'

/** «2026-11-08T09:00» para `<input type="datetime-local">`, en hora local. */
function toLocalInput(iso: string | null) {
  if (!iso) return ''
  const date = new Date(iso)
  return new Date(date.getTime() - date.getTimezoneOffset() * 60_000).toISOString().slice(0, 16)
}

/** /forms/:uuid/edit — solo quien lo creó. */
export function FormEditorPage() {
  const uuid = useParams().formId ?? ''
  const form = useQuery({ queryKey: formsKeys.detail(uuid), queryFn: () => formsApi.get(uuid) })
  const can = useCan()
  useDocumentTitle(form.data ? `Editar: ${form.data.title}` : 'Editar formulario')
  const back = (
    <Link to="/forms?view=mine" className="inline-flex w-fit items-center gap-2 rounded-lg text-sm font-semibold text-slate-500 hover:text-slate-800">
      <ArrowLeft className="size-4" aria-hidden /> Mis formularios
    </Link>
  )
  if (form.isPending) return <div className="grid gap-4">{back}<Card className="grid gap-3 p-6"><Skeleton className="h-10 w-2/3" /><Skeleton className="h-20" /></Card></div>
  // Editar: quien lo creó, o alguien con «forms.forms.update.all» (moderación).
  if (form.isError || !(form.data.is_mine || can('forms.forms.update.all'))) {
    const gone = form.isError && isAxiosError(form.error) && form.error.response?.status === 404
    return <div className="grid gap-4">{back}<Card><EmptyState icon={form.isError ? FileX : Lock} title={gone ? 'Este formulario no está disponible' : form.isError ? 'No se pudo cargar' : 'Solo quien lo creó puede editarlo'} /></Card></div>
  }
  return (
    <div className="grid gap-4">
      {back}
      <FormTabs uuid={uuid} count={form.data.submissions_count} results={form.data.is_mine || can('forms.forms.view.all') || can('forms.submissions.view.all')} />
      <Editor form={form.data} />
    </div>
  )
}

type Draft = Question & { _key: string }
const withKeys = (questions: Question[]): Draft[] => questions.map((question) => ({ ...question, _key: crypto.randomUUID() }))

function Editor({ form }: { form: FormDetail }) {
  const can = useCan()
  const canDelete = form.is_mine || can('forms.forms.delete.all')
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [title, setTitle] = useState(form.title)
  const [description, setDescription] = useState(form.description)
  const [oneEach, setOneEach] = useState(form.one_submission_per_user)
  const [closesAt, setClosesAt] = useState(toLocalInput(form.closes_at))
  const [questions, setQuestions] = useState<Draft[]>(() => withKeys(form.questions))
  const [dirty, setDirty] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const touch = () => setDirty(true)

  // Avisar antes de salir con cambios sin guardar (otra ruta o cerrar la pestaña).
  const blocker = useBlocker(({ currentLocation, nextLocation }) => dirty && currentLocation.pathname !== nextLocation.pathname)
  useEffect(() => {
    if (blocker.state === 'blocked') {
      if (window.confirm('Tienes cambios sin guardar. ¿Salir de todos modos?')) blocker.proceed()
      else blocker.reset()
    }
  }, [blocker])
  useEffect(() => {
    if (!dirty) return
    const warn = (event: BeforeUnloadEvent) => event.preventDefault()
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])

  const save = useMutation({
    mutationFn: async (status?: FormStatus) => {
      await formsApi.update(form.uuid, { title: title.trim(), description: description.trim(), one_submission_per_user: oneEach, closes_at: closesAt ? new Date(closesAt).toISOString() : null })
      let saved = await formsApi.saveQuestions(form.uuid, questions)
      if (status && status !== saved.status) saved = await formsApi.update(form.uuid, { status })
      return saved
    },
    onSuccess: (saved, status) => {
      queryClient.setQueryData(formsKeys.detail(form.uuid), saved)
      void queryClient.invalidateQueries({ queryKey: formsKeys.lists() })
      setQuestions(withKeys(saved.questions))
      setDirty(false)
      setError(null)
      toast.success(status === 'open' ? 'Formulario abierto: ya recibe respuestas.' : status === 'closed' ? 'Formulario cerrado.' : status === 'draft' ? 'Regresó a borrador.' : 'Cambios guardados.')
    },
    onError: (err) => setError(getErrorMessage(err, 'No se pudo guardar.')),
  })
  const remove = useMutation({
    mutationFn: () => formsApi.remove(form.uuid),
    onSuccess: () => {
      setDirty(false)
      void queryClient.invalidateQueries({ queryKey: formsKeys.lists() })
      toast('Formulario eliminado.')
      navigate('/forms?view=mine', { replace: true })
    },
    onError: (err) => toast.error(getErrorMessage(err, 'No se pudo eliminar.')),
  })

  const setQuestion = (index: number, question: Question) => { setQuestions((list) => list.map((item, i) => (i === index ? { ...question, _key: item._key } : item))); touch() }
  function move(index: number, delta: -1 | 1) {
    setQuestions((list) => { const next = [...list]; [next[index], next[index + delta]] = [next[index + delta], next[index]]; return next })
    touch()
  }
  function add() {
    setQuestions((list) => [...list, { ...blankQuestion(), _key: crypto.randomUUID() }])
    touch()
    requestAnimationFrame(() => document.querySelector<HTMLInputElement>('[data-question]:last-of-type input')?.focus())
  }
  const link = `${window.location.origin}/forms/${form.uuid}`

  return (
    <>
      <Card className="overflow-hidden">
        <div className="h-2 bg-brand-500" aria-hidden />
        <div className="grid gap-2 p-5 sm:p-6">
          <input value={title} onChange={(event) => { setTitle(event.target.value); touch() }} maxLength={200} placeholder="Título del formulario" aria-label="Título del formulario"
            className="border-b border-transparent bg-transparent pb-1 font-display text-2xl font-bold text-slate-900 placeholder:text-slate-300 hover:border-slate-200 focus:border-brand-500 focus:outline-none sm:text-3xl" />
          <textarea value={description} onChange={(event) => { setDescription(event.target.value); touch() }} maxLength={2000} rows={2} placeholder="Descripción (opcional)" aria-label="Descripción"
            className="field-sizing-content resize-none border-b border-transparent bg-transparent text-sm text-slate-600 placeholder:text-slate-400 hover:border-slate-200 focus:border-brand-500 focus:outline-none" />
        </div>
      </Card>

      <Card className="grid gap-4 p-4 sm:p-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className={cn('rounded-full px-2.5 py-1 text-xs font-bold', form.status === 'open' ? 'bg-emerald-50 text-emerald-700' : form.status === 'draft' ? 'bg-amber-50 text-amber-700' : 'bg-slate-100 text-slate-600')}>
            {form.status === 'open' ? (form.accepting ? 'Abierto · recibe respuestas' : 'Abierto · fuera de fechas') : form.status === 'draft' ? 'Borrador · nadie lo ve' : 'Cerrado'}
          </span>
          {form.status !== 'draft' && (
            <Button size="sm" variant="ghost" onClick={() => { void navigator.clipboard.writeText(link); toast.success('Enlace copiado.') }}><Copy className="size-4" aria-hidden /> Copiar enlace</Button>
          )}
          <div className="ml-auto flex gap-2">
            {form.status !== 'open' && <Button size="sm" variant="soft" loading={save.isPending && save.variables === 'open'} disabled={save.isPending} onClick={() => save.mutate('open')}>{form.status === 'draft' ? 'Publicar' : 'Reabrir'}</Button>}
            {form.status === 'open' && <Button size="sm" variant="outline" loading={save.isPending && save.variables === 'closed'} disabled={save.isPending} onClick={() => window.confirm('¿Cerrar el formulario? Ya no recibirá respuestas.') && save.mutate('closed')}>Cerrar</Button>}
          </div>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 p-3 select-none">
            <input type="checkbox" checked={oneEach} onChange={(event) => { setOneEach(event.target.checked); touch() }} className="mt-0.5 size-4 accent-brand-500" />
            <span><span className="block text-sm font-semibold text-slate-800">Una respuesta por persona</span><span className="block text-xs text-slate-500">Desactívalo para registros que se llenan varias veces.</span></span>
          </label>
          <label className="grid gap-1 rounded-xl border border-slate-200 p-3">
            <span className="text-sm font-semibold text-slate-800">Cierra solo el (opcional)</span>
            <input type="datetime-local" value={closesAt} onChange={(event) => { setClosesAt(event.target.value); touch() }}
              className="h-9 rounded-lg border border-slate-200 px-2 text-base focus:border-brand-500 focus:outline-none sm:text-sm" />
          </label>
        </div>
      </Card>

      {error && <Alert tone="error">{error}</Alert>}

      <ol className="grid gap-4">
        {questions.map((question, index) => (
          <li key={question._key} data-question>
            <QuestionEditor
              question={question} number={index + 1} total={questions.length}
              onChange={(next) => setQuestion(index, next)}
              onMove={(delta) => move(index, delta)}
              onDuplicate={() => { setQuestions((list) => [...list.slice(0, index + 1), { ...question, id: undefined, has_answers: false, options: question.options.map(({ text }) => ({ text })), rows: question.rows.map(({ text }) => ({ text })), _key: crypto.randomUUID() }, ...list.slice(index + 1)]); touch() }}
              onRemove={() => {
                if (question.has_answers && !window.confirm('Esta pregunta ya tiene respuestas. Al guardar se borrarán también. ¿Quitarla?')) return
                setQuestions((list) => list.filter((_, i) => i !== index)); touch()
              }}
            />
          </li>
        ))}
      </ol>
      {questions.length === 0 && <Card><EmptyState icon={Plus} title="Agrega la primera pregunta" description="Respuesta corta, opciones, escalas, cuadrículas, fecha…" /></Card>}
      <Button variant="outline" className="w-full border-dashed" onClick={add}><Plus className="size-4" aria-hidden /> Agregar pregunta</Button>

      <div className="sticky bottom-[calc(5rem+env(safe-area-inset-bottom))] z-20 flex items-center gap-2 rounded-2xl border border-slate-200 bg-surface/95 p-3 shadow-lg backdrop-blur lg:bottom-4">
        {canDelete && (
          <Button variant="ghost" className="text-red-600 hover:bg-red-50 hover:text-red-700" aria-label="Eliminar formulario" loading={remove.isPending}
            onClick={() => window.confirm(`¿Eliminar «${form.title}»? Dejará de verse para todos${form.submissions_count ? ' (sus respuestas se conservan en el sistema)' : ''}.`) && remove.mutate()}>
            <Trash2 className="size-4" aria-hidden />
          </Button>
        )}
        <span className="ml-auto text-xs text-slate-500">{dirty ? 'Cambios sin guardar' : <span className="flex items-center gap-1"><Check className="size-3.5" aria-hidden /> Guardado</span>}</span>
        <Button loading={save.isPending && save.variables === undefined} disabled={save.isPending || !dirty} onClick={() => save.mutate(undefined)}>Guardar</Button>
      </div>
    </>
  )
}
