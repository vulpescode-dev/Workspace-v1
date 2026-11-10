import { useMutation } from '@tanstack/react-query'
import { UploadCloud } from 'lucide-react'
import { useRef, useState, type FormEvent } from 'react'
import { toast } from 'sonner'
import { Sheet } from '@/components/ui/Sheet'

import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { getErrorMessage } from '@/lib/api/errors'

import { documentsApi } from '../api/documents.api'
import { formatSize } from '../utils'
import { FileTypeIcon } from './FileTypeIcon'

const MAX_BYTES = 20 * 1024 * 1024
const ACCEPT = '.pdf,.docx,.xlsx,.pptx,.csv,.txt,.png,.jpg,.jpeg,.webp'

/** Nueva versión: archivo y qué cambió (opcional). Queda como la vigente; la anterior pasa al historial. */
export function NewVersionSheet({ documentId, nextNumber, onDone, onClose }: { documentId: number; nextNumber: number; onDone: () => void; onClose: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [notes, setNotes] = useState('')
  const [error, setError] = useState<string | null>(null)

  const upload = useMutation({
    mutationFn: () => {
      const form = new FormData()
      form.append('file', file!)
      form.append('notes', notes.trim())
      return documentsApi.addVersion(documentId, form)
    },
    onSuccess: () => { toast.success(`Versión ${nextNumber} publicada.`); onDone(); onClose() },
    onError: (err) => setError(getErrorMessage(err, 'No se pudo subir la versión.')),
  })

  function pick(next: File | undefined) {
    if (!next) return
    if (next.size > MAX_BYTES) return setError('El archivo pesa más de 20 MB.')
    setError(null)
    setFile(next)
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!file) return setError('Elige el archivo de la nueva versión.')
    upload.mutate()
  }

  return (
    <Sheet open onOpenChange={(open) => !open && onClose()} title={<>Nueva versión (v{nextNumber})</>}>
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
            <span className="block truncate text-sm font-semibold text-slate-900">{file ? file.name : 'Elige o arrastra el archivo'}</span>
            <span className="block text-xs text-slate-500">{file ? formatSize(file.size) : 'PDF, Word, Excel, PowerPoint, CSV, TXT o imagen · hasta 20 MB'}</span>
          </span>
        </button>
        <input ref={inputRef} type="file" accept={ACCEPT} hidden onChange={(event) => { pick(event.target.files?.[0]); event.target.value = '' }} />
        <Field label="¿Qué cambió? (opcional)" hint="Ayuda a quien lo consulta a saber si debe volver a leerlo.">
          {({ invalid, ...props }) => (
            <textarea {...props} aria-invalid={invalid || undefined} value={notes} onChange={(event) => setNotes(event.target.value)} maxLength={500} rows={3}
              placeholder="Ej.: Se actualizó la tabla de viáticos"
              className="w-full resize-none rounded-xl border border-slate-200 bg-surface px-4 py-3 text-base text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm" />
          )}
        </Field>
        <div className="flex justify-end gap-2 pt-1">
          <Button variant="ghost" onClick={onClose}>Cancelar</Button>
          <Button type="submit" loading={upload.isPending}>Publicar versión</Button>
        </div>
      </form>
    </Sheet>
  )
}
