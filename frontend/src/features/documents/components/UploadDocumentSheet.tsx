import { useMutation, useQueryClient } from '@tanstack/react-query'
import { UploadCloud } from 'lucide-react'
import { useRef, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'
import { Sheet } from '@/components/ui/Sheet'

import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { Input } from '@/components/ui/Input'
import { getErrorMessage } from '@/lib/api/errors'

import { documentsApi, documentsKeys, type DocumentCategory } from '../api/documents.api'
import { formatSize } from '../utils'
import { appendAudience, audienceError, type Audience } from '../audience'
import { AudiencePicker } from './AudiencePicker'
import { FileTypeIcon } from './FileTypeIcon'

const MAX_BYTES = 20 * 1024 * 1024
const ACCEPT = '.pdf,.docx,.xlsx,.pptx,.csv,.txt,.png,.jpg,.jpeg,.webp'
const selectClass = 'h-12 w-full rounded-xl border border-slate-200 bg-surface px-3 text-base text-slate-900 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm'

/**
 * Subir un documento: archivo (PDF, Office moderno, CSV/TXT o imagen, hasta 20 MB; el servidor revisa el
 * contenido), título (se propone el nombre del archivo), categoría, descripción y quién lo ve.
 */
export function UploadDocumentSheet({ categories, onClose }: { categories: DocumentCategory[]; onClose: () => void }) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [category, setCategory] = useState(categories[0]?.id ?? 0)
  const [description, setDescription] = useState('')
  const [audience, setAudience] = useState<Audience>({ visibility: 'public', departments: [], people: [] })
  const [error, setError] = useState<string | null>(null)

  const upload = useMutation({
    mutationFn: () => {
      const form = new FormData()
      form.append('file', file!)
      form.append('title', title.trim())
      form.append('category', String(category))
      form.append('description', description.trim())
      appendAudience(form, audience)
      return documentsApi.create(form)
    },
    onSuccess: (document) => {
      void queryClient.invalidateQueries({ queryKey: documentsKeys.lists() })
      toast.success('Documento publicado.')
      onClose()
      navigate(`/documents/${document.id}`)
    },
    onError: (err) => setError(getErrorMessage(err, 'No se pudo subir el documento.')),
  })

  function pick(next: File | undefined) {
    if (!next) return
    if (next.size > MAX_BYTES) return setError('El archivo pesa más de 20 MB.')
    setError(null)
    setFile(next)
    if (!title) setTitle(next.name.replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' '))
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!file || !title.trim() || !category) return setError('Elige un archivo, escribe un título y elige una categoría.')
    const invalid = audienceError(audience)
    if (invalid) return setError(invalid)
    upload.mutate()
  }

  return (
    <Sheet open onOpenChange={(open) => !open && onClose()} title="Subir documento">

      {categories.length === 0 ? (
        <div className="px-5 pb-4">
          <Alert tone="info">Aún no hay categorías de documentos. Pide a Soporte TI que las cree en el administrador.</Alert>
        </div>
      ) : (
        <form onSubmit={submit} className="grid gap-4 overflow-y-auto px-5 pb-2">
          {error && <Alert tone="error">{error}</Alert>}
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => { event.preventDefault(); pick(event.dataTransfer.files[0]) }}
            className="pressable flex items-center gap-3 rounded-2xl border-2 border-dashed border-slate-200 p-4 text-left transition-colors duration-150 hover:border-brand-300 hover:bg-brand-50/40"
          >
            {file ? <FileTypeIcon contentType={file.type} name={file.name} /> : <span className="grid size-11 place-items-center rounded-xl bg-brand-50 text-brand-600"><UploadCloud className="size-5" aria-hidden /></span>}
            <span className="min-w-0">
              <span className="block truncate text-sm font-semibold text-slate-900">{file ? file.name : 'Elige o arrastra un archivo'}</span>
              <span className="block text-xs text-slate-500">{file ? formatSize(file.size) : 'PDF, Word, Excel, PowerPoint, CSV, TXT o imagen · hasta 20 MB'}</span>
            </span>
          </button>
          <input ref={inputRef} type="file" accept={ACCEPT} hidden onChange={(event) => { pick(event.target.files?.[0]); event.target.value = '' }} />

          <Field label="Título">{(props) => <Input {...props} value={title} onChange={(event) => setTitle(event.target.value)} maxLength={150} />}</Field>
          <Field label="Categoría">
            {({ invalid, ...props }) => (
              <select {...props} aria-invalid={invalid || undefined} value={category} onChange={(event) => setCategory(Number(event.target.value))} className={selectClass}>
                {categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
              </select>
            )}
          </Field>
          <Field label="Descripción (opcional)">{(props) => <Input {...props} value={description} onChange={(event) => setDescription(event.target.value)} />}</Field>

          <AudiencePicker value={audience} onChange={setAudience} />

          <div className="flex justify-end gap-2 pt-1">
            <Button variant="ghost" onClick={onClose}>Cancelar</Button>
            <Button type="submit" loading={upload.isPending}>Publicar</Button>
          </div>
        </form>
      )}
    </Sheet>
  )
}
