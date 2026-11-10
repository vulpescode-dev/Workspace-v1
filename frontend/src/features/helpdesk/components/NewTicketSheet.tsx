import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CircleHelp } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'

import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Combobox, type ComboboxOption } from '@/components/ui/Combobox'
import { Field } from '@/components/ui/Field'
import { Input } from '@/components/ui/Input'
import { Sheet } from '@/components/ui/Sheet'
import { getErrorMessage } from '@/lib/api/errors'

import { helpdeskApi, helpdeskKeys } from '../api/helpdesk.api'
import { FilePicker } from './TicketFiles'

const KIND_LABELS = { incident: 'Algo no funciona', request: 'Necesito algo' } as const
/** Valor de «Otro» en la lista: el ticket se manda sin categoría. */
const OTHER = -1

/**
 * Levantar un ticket. Primero se elige el problema en un select con búsqueda (cada uno ya sabe qué
 * departamento lo atiende); si no está, «Otro» lo manda sin clasificar a los agentes de todos los
 * departamentos y el que sepa de qué trata lo clasifica. Luego título, qué pasa y hasta 5 archivos.
 */
export function NewTicketSheet({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const categories = useQuery({ queryKey: helpdeskKeys.categories(), queryFn: helpdeskApi.categories, staleTime: 10 * 60_000 })
  const [category, setCategory] = useState(0)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [error, setError] = useState<string | null>(null)

  const options: ComboboxOption<number>[] = [
    ...(categories.data ?? []).map((item) => ({ value: item.id, label: item.name, description: item.description || KIND_LABELS[item.kind], group: item.department.name })),
    { value: OTHER, label: 'Otro: no está en la lista', description: 'Lo verán todas las áreas y la que corresponda lo tomará.', icon: <CircleHelp className="size-4" />, pinned: true },
  ]
  const selected = categories.data?.find((item) => item.id === category)
  const hint = selected
    ? `Lo atiende ${selected.department.name}.`
    : category === OTHER ? 'Sin área asignada todavía: quien sepa de qué trata lo clasifica.' : 'Escribe para buscar. Si no está, elige «Otro».'

  const create = useMutation({
    mutationFn: () => {
      const form = new FormData()
      if (category !== OTHER) form.append('category', String(category))
      form.append('title', title.trim())
      form.append('description', description.trim())
      files.forEach((file) => form.append('files', file))
      return helpdeskApi.create(form)
    },
    onSuccess: (ticket) => {
      queryClient.setQueryData(helpdeskKeys.detail(ticket.id), ticket)
      void queryClient.invalidateQueries({ queryKey: helpdeskKeys.lists() })
      toast.success(ticket.department
        ? `Ticket ${ticket.folio} enviado a ${ticket.department.name}.`
        : `Ticket ${ticket.folio} enviado. El área que corresponda lo tomará.`)
      onClose()
      navigate(`/helpdesk/${ticket.id}`)
    },
    onError: (err) => setError(getErrorMessage(err, 'No se pudo enviar el ticket.')),
  })

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!category) return setError('Elige de qué se trata (o «Otro» si no está en la lista).')
    if (!title.trim() || !description.trim()) return setError('Escribe un título y cuéntanos qué pasa.')
    setError(null)
    create.mutate()
  }

  return (
    <Sheet open onOpenChange={(open) => !open && onClose()} repositionInputs={false} title="Nuevo ticket">
      <form onSubmit={submit} className="grid gap-4 overflow-y-auto px-5 pb-2">
        {error && <Alert tone="error">{error}</Alert>}

        <Field label="¿De qué se trata?" hint={hint}>
          {(props) => (
            <Combobox {...props} options={options} value={category || null} onChange={setCategory} loading={categories.isPending}
              placeholder="Busca tu problema: VPN, nómina, vacaciones…" emptyText="No está en la lista: elige «Otro»." />
          )}
        </Field>

        <Field label="Título">{(props) => <Input {...props} value={title} onChange={(event) => setTitle(event.target.value)} maxLength={150} placeholder="Ej.: No puedo entrar a la VPN" />}</Field>
        <Field label="¿Qué pasa?" hint="Desde cuándo, qué intentaste y qué mensaje aparece. Una captura ayuda mucho.">
          {({ invalid, ...props }) => (
            <textarea {...props} aria-invalid={invalid || undefined} value={description} onChange={(event) => setDescription(event.target.value)} maxLength={5000} rows={5}
              className="w-full resize-none rounded-xl border border-slate-200 bg-surface px-4 py-3 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm" />
          )}
        </Field>
        <FilePicker files={files} onChange={setFiles} />
        <div className="flex justify-end gap-2 pt-1">
          <Button variant="ghost" onClick={onClose}>Cancelar</Button>
          <Button type="submit" loading={create.isPending}>Enviar ticket</Button>
        </div>
      </form>
    </Sheet>
  )
}
