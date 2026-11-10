import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'
import { Sheet } from '@/components/ui/Sheet'

import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { Input } from '@/components/ui/Input'
import { getErrorMessage } from '@/lib/api/errors'

import { documentsApi, documentsKeys, type DocumentDetail } from '../api/documents.api'
import { audienceError, type Audience } from '../audience'
import { AudiencePicker } from './AudiencePicker'

const selectClass = 'h-12 w-full rounded-xl border border-slate-200 bg-surface px-3 text-base text-slate-900 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm'

/**
 * Editar la ficha (título, categoría, descripción) y con quién se comparte. Solo se manda lo que cambió.
 * Si quien edita deja de poder verlo (p. ej. alguien con `manage` lo comparte solo con otras personas),
 * regresa a la lista.
 */
export function EditDocumentSheet({ document, onClose }: { document: DocumentDetail; onClose: () => void }) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const categories = useQuery({ queryKey: documentsKeys.categories(), queryFn: documentsApi.categories, staleTime: 10 * 60_000 })
  const [title, setTitle] = useState(document.title)
  const [category, setCategory] = useState(document.category.id)
  const [description, setDescription] = useState(document.description)
  const initialAudience: Audience = { visibility: document.visibility, departments: document.departments?.map((d) => d.id) ?? [], people: document.shared_with ?? [] }
  const [audience, setAudience] = useState<Audience>(initialAudience)
  const [error, setError] = useState<string | null>(null)
  // La categoría actual puede estar desactivada: se sigue mostrando para no cambiarla sin querer.
  const options = categories.data?.some((item) => item.id === document.category.id) === false ? [document.category, ...categories.data] : categories.data ?? [document.category]

  const save = useMutation({
    mutationFn: () => {
      const changes: Record<string, unknown> = {}
      if (title.trim() !== document.title) changes.title = title.trim()
      if (description.trim() !== document.description) changes.description = description.trim()
      if (category !== document.category.id) changes.category = category
      if (JSON.stringify(audience) !== JSON.stringify(initialAudience)) {
        changes.visibility = audience.visibility
        changes.departments = audience.visibility === 'departments' ? audience.departments : []
        changes.users = audience.visibility === 'users' ? audience.people.map((person) => person.id) : []
      }
      return documentsApi.update(document.id, changes)
    },
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: documentsKeys.lists() })
      onClose()
      if ('visible' in result) {
        toast.success('Cambios guardados. Ya no tienes acceso a este documento.')
        queryClient.removeQueries({ queryKey: documentsKeys.detail(document.id) })
        navigate('/documents', { replace: true })
        return
      }
      queryClient.setQueryData(documentsKeys.detail(document.id), result)
      toast.success('Cambios guardados.')
    },
    onError: (err) => setError(getErrorMessage(err, 'No se pudieron guardar los cambios.')),
  })

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!title.trim()) return setError('Escribe un título.')
    const invalid = audienceError(audience)
    if (invalid) return setError(invalid)
    save.mutate()
  }

  return (
    <Sheet open onOpenChange={(open) => !open && onClose()} title="Editar documento">
      <form onSubmit={submit} className="grid gap-4 overflow-y-auto px-5 pb-2">
        {error && <Alert tone="error">{error}</Alert>}
        <Field label="Título">{(props) => <Input {...props} value={title} onChange={(event) => setTitle(event.target.value)} maxLength={150} />}</Field>
        <Field label="Categoría">
          {({ invalid, ...props }) => (
            <select {...props} aria-invalid={invalid || undefined} value={category} onChange={(event) => setCategory(Number(event.target.value))} className={selectClass}>
              {options.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          )}
        </Field>
        <Field label="Descripción (opcional)">{(props) => <Input {...props} value={description} onChange={(event) => setDescription(event.target.value)} maxLength={2000} />}</Field>
        <AudiencePicker value={audience} onChange={setAudience} />
        <div className="flex justify-end gap-2 pt-1">
          <Button variant="ghost" onClick={onClose}>Cancelar</Button>
          <Button type="submit" loading={save.isPending}>Guardar</Button>
        </div>
      </form>
    </Sheet>
  )
}
