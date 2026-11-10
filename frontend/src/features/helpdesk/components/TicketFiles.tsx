import { Download, Paperclip, X } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { FileTypeIcon } from '@/features/documents/components/FileTypeIcon'
import { formatSize } from '@/features/documents/utils'
import { getErrorMessage } from '@/lib/api/errors'
import { downloadProtected } from '@/lib/media/download'

import { MAX_TICKET_FILES, type TicketAttachment } from '../api/helpdesk.api'

const MAX_BYTES = 20 * 1024 * 1024
const TICKET_ACCEPT = '.pdf,.docx,.xlsx,.pptx,.csv,.txt,.png,.jpg,.jpeg,.webp'

/** Adjuntos ya subidos: tocar uno lo descarga con sesión y con su nombre original. */
export function AttachmentList({ files }: { files: TicketAttachment[] }) {
  const [busy, setBusy] = useState<number | null>(null)
  if (!files.length) return null
  async function download(file: TicketAttachment) {
    setBusy(file.id)
    try { await downloadProtected(file.url, file.name) } catch (error) { toast.error(getErrorMessage(error, 'No se pudo descargar.')) } finally { setBusy(null) }
  }
  return (
    <ul className="mt-2 flex flex-wrap gap-2">
      {files.map((file) => (
        <li key={file.id}>
          <button type="button" onClick={() => void download(file)} disabled={busy === file.id}
            className="pressable flex max-w-64 items-center gap-2 rounded-xl border border-slate-200 bg-surface py-1.5 pr-3 pl-1.5 text-left transition-colors duration-150 hover:bg-slate-50 disabled:opacity-60">
            <FileTypeIcon contentType={file.content_type} name={file.name} className="size-8 rounded-lg [&_svg]:size-4" />
            <span className="min-w-0">
              <span className="block truncate text-xs font-semibold text-slate-800">{file.name}</span>
              <span className="block text-[11px] text-slate-500">{formatSize(file.size)}</span>
            </span>
            <Download className="size-3.5 shrink-0 text-slate-400" aria-hidden />
          </button>
        </li>
      ))}
    </ul>
  )
}

/**
 * Archivos por adjuntar (hasta 5, ≤ 20 MB; el servidor revisa el contenido). Muestra un clip para elegir
 * y las elegidas como pastillas con ✕.
 */
export function FilePicker({ files, onChange, compact = false }: { files: File[]; onChange: (files: File[]) => void; compact?: boolean }) {
  const input = useRef<HTMLInputElement>(null)
  function pick(list: FileList | null) {
    const picked = Array.from(list ?? [])
    const tooBig = picked.filter((file) => file.size > MAX_BYTES)
    if (tooBig.length) toast.error(`«${tooBig[0].name}» pesa más de 20 MB.`)
    const next = [...files, ...picked.filter((file) => file.size <= MAX_BYTES)]
    if (next.length > MAX_TICKET_FILES) toast.error(`Máximo ${MAX_TICKET_FILES} archivos por mensaje.`)
    onChange(next.slice(0, MAX_TICKET_FILES))
  }
  return (
    <div className="flex flex-wrap items-center gap-2">
      <button type="button" onClick={() => input.current?.click()} disabled={files.length >= MAX_TICKET_FILES}
        aria-label={compact ? 'Adjuntar archivos' : undefined}
        className="pressable flex h-9 items-center gap-1.5 rounded-xl px-2.5 text-sm font-semibold text-slate-600 transition-colors duration-150 hover:bg-slate-100 disabled:opacity-50">
        <Paperclip className="size-4" aria-hidden /> {!compact && 'Adjuntar archivos'}
      </button>
      {files.map((file, index) => (
        <span key={`${file.name}-${index}`} className="flex h-8 max-w-52 items-center gap-1.5 rounded-full bg-slate-100 pr-1 pl-3 text-xs font-medium text-slate-700">
          <span className="truncate">{file.name}</span>
          <button type="button" aria-label={`Quitar ${file.name}`} onClick={() => onChange(files.filter((_, i) => i !== index))}
            className="grid size-6 shrink-0 place-items-center rounded-full hover:bg-slate-200">
            <X className="size-3.5" aria-hidden />
          </button>
        </span>
      ))}
      <input ref={input} type="file" accept={TICKET_ACCEPT} multiple hidden onChange={(event) => { pick(event.target.files); event.target.value = '' }} />
    </div>
  )
}
