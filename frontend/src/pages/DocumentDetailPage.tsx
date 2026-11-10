import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { ArrowLeft, Download, FileX, History, Pencil, RotateCcw, Trash2, Upload } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'

import { useCan } from '@/features/accounts/hooks/useCan'
import { EmptyState } from '@/components/feedback/EmptyState'
import { ListSkeleton } from '@/components/feedback/ListSkeleton'
import { Skeleton } from '@/components/feedback/Skeleton'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { UserAvatar } from '@/features/accounts/components/UserAvatar'
import { documentsApi, documentsKeys, VISIBILITY_LABELS, type DocumentVersion } from '@/features/documents/api/documents.api'
import { EditDocumentSheet } from '@/features/documents/components/EditDocumentSheet'
import { FileTypeIcon } from '@/features/documents/components/FileTypeIcon'
import { NewVersionSheet } from '@/features/documents/components/NewVersionSheet'
import { fileKindLabel, formatSize, VISIBILITY_ICONS } from '@/features/documents/utils'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'
import { getErrorMessage } from '@/lib/api/errors'
import { cn } from '@/lib/cn'
import { formatFullDateTime, formatRelative } from '@/lib/format'
import { downloadProtected } from '@/lib/media/download'

/** /documents/:id — ficha, descargar la versión vigente e historial (cada versión se descarga o restaura). */
export function DocumentDetailPage() {
  const can = useCan()
  const id = Number(useParams().documentId)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const doc = useQuery({ queryKey: documentsKeys.detail(id), queryFn: () => documentsApi.get(id), enabled: Number.isInteger(id) })
  const [sheet, setSheet] = useState<'edit' | 'version' | null>(null)
  const [downloading, setDownloading] = useState<number | null>(null)
  useDocumentTitle(doc.data?.title ?? 'Documento')

  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: documentsKeys.detail(id) })
    void queryClient.invalidateQueries({ queryKey: documentsKeys.lists() })
  }
  const fail = (fallback: string) => (error: unknown) => toast.error(getErrorMessage(error, fallback))
  const restore = useMutation({
    mutationFn: (version: DocumentVersion) => documentsApi.restore(id, version.id),
    onSuccess: () => { toast.success('Versión restaurada como la vigente.'); refresh() },
    onError: fail('No se pudo restaurar.'),
  })
  const remove = useMutation({
    mutationFn: () => documentsApi.remove(id),
    onSuccess: () => { toast('Documento eliminado.'); void queryClient.invalidateQueries({ queryKey: documentsKeys.lists() }); navigate('/documents', { replace: true }) },
    onError: fail('No se pudo eliminar.'),
  })

  async function download(version: DocumentVersion) {
    setDownloading(version.id)
    try { await downloadProtected(version.url, version.name) } catch (error) { toast.error(getErrorMessage(error, 'No se pudo descargar.')) } finally { setDownloading(null) }
  }

  const back = (
    <Link to="/documents" className="inline-flex w-fit items-center gap-2 rounded-lg text-sm font-semibold text-slate-500 hover:text-slate-800">
      <ArrowLeft className="size-4" aria-hidden /> Documentos
    </Link>
  )

  if (doc.isPending) {
    return <div className="grid gap-4">{back}<Card className="flex gap-4 p-5"><Skeleton className="size-14 rounded-2xl" /><div className="grid flex-1 gap-2"><Skeleton className="h-6 w-2/3" /><Skeleton className="h-4 w-1/2" /></div></Card><Card className="p-5"><ListSkeleton rows={3} /></Card></div>
  }
  if (doc.isError) {
    const gone = isAxiosError(doc.error) && doc.error.response?.status === 404
    return <div className="grid gap-4">{back}<Card><EmptyState icon={FileX} title={gone ? 'Este documento no está disponible' : 'No se pudo cargar el documento'} description={gone ? 'Puede que se haya eliminado o que no tengas acceso.' : undefined} /></Card></div>
  }

  const data = doc.data
  const current = data.current_version
  // Descargar: quien administra el documento siempre; los demás, con «documents.documents.download».
  const canDownload = data.can_manage || can('documents.documents.download')
  const VisibilityIcon = VISIBILITY_ICONS[data.visibility]
  const sharedWith = data.visibility === 'departments' ? data.departments?.map((d) => d.name) : data.visibility === 'users' ? data.shared_with?.map((u) => u.name) : null

  return (
    <div className="grid gap-4">
      {back}
      <Card className="p-5 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
          <FileTypeIcon contentType={current?.content_type} name={current?.name} className="size-14 rounded-2xl [&_svg]:size-7" />
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-bold text-slate-900 sm:text-2xl">{data.title}</h1>
            {data.description && <p className="mt-1 text-sm text-slate-600">{data.description}</p>}
            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
              <span className="rounded-full bg-slate-100 px-2.5 py-1 font-medium text-slate-700">{data.category.name}</span>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 font-medium text-slate-700"><VisibilityIcon className="size-3.5" aria-hidden />{VISIBILITY_LABELS[data.visibility]}</span>
              {current && <span>{fileKindLabel(current.content_type, current.name)} · {formatSize(current.size)} · v{current.number}</span>}
            </div>
            {sharedWith && sharedWith.length > 0 && <p className="mt-2 text-xs text-slate-500">Compartido con: {sharedWith.join(', ')}</p>}
          </div>
          <div className="flex flex-wrap gap-2">
            {current && canDownload && <Button onClick={() => void download(current)} loading={downloading === current.id}><Download className="size-4" aria-hidden /> Descargar</Button>}
            {data.can_manage && <Button variant="outline" onClick={() => setSheet('version')}><Upload className="size-4" aria-hidden /> Nueva versión</Button>}
            {data.can_manage && <Button variant="ghost" aria-label="Editar ficha y con quién se comparte" onClick={() => setSheet('edit')}><Pencil className="size-4" aria-hidden /></Button>}
            {data.can_manage && (
              <Button variant="ghost" aria-label="Eliminar documento" onClick={() => window.confirm('¿Eliminar este documento? Dejará de verse para todos.') && remove.mutate()}>
                <Trash2 className="size-4 text-red-500" aria-hidden />
              </Button>
            )}
          </div>
        </div>
      </Card>

      <Card className="p-5 sm:p-6">
        <h2 className="mb-4 flex items-center gap-2 text-base font-bold text-slate-900"><History className="size-5 text-slate-400" aria-hidden /> Historial de versiones</h2>
        <ol className="relative grid gap-5 border-l border-slate-200 pl-6">
          {data.versions.map((version) => {
            const isCurrent = version.id === current?.id
            return (
              <li key={version.id} className="relative">
                <span className={cn('absolute top-1 -left-[31px] size-3 rounded-full ring-4 ring-surface', isCurrent ? 'bg-brand-500' : 'bg-slate-300')} aria-hidden />
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-900">
                      Versión {version.number}
                      {isCurrent && <span className="ml-2 rounded-full bg-brand-50 px-2 py-0.5 text-xs font-semibold text-brand-700">Vigente</span>}
                    </p>
                    {version.notes && <p className="mt-0.5 text-sm text-slate-600">{version.notes}</p>}
                    <p className="mt-1.5 flex items-center gap-2 text-xs text-slate-500">
                      <UserAvatar user={version.uploaded_by} size="sm" />
                      {version.uploaded_by.name} · <time title={formatFullDateTime(version.created_at)}>{formatRelative(version.created_at)}</time> · {formatSize(version.size)}
                    </p>
                  </div>
                  <div className="flex gap-1">
                    {canDownload && <Button variant="ghost" size="sm" onClick={() => void download(version)} loading={downloading === version.id}><Download className="size-4" aria-hidden /> Descargar</Button>}
                    {data.can_manage && !isCurrent && (
                      <Button variant="ghost" size="sm" loading={restore.isPending && restore.variables?.id === version.id} onClick={() => window.confirm(`¿Restaurar la versión ${version.number}? Se copiará como versión nueva.`) && restore.mutate(version)}>
                        <RotateCcw className="size-4" aria-hidden /> Restaurar
                      </Button>
                    )}
                  </div>
                </div>
              </li>
            )
          })}
        </ol>
      </Card>

      {sheet === 'edit' && <EditDocumentSheet document={data} onClose={() => setSheet(null)} />}
      {sheet === 'version' && <NewVersionSheet documentId={id} nextNumber={Math.max(0, ...data.versions.map((v) => v.number)) + 1} onDone={refresh} onClose={() => setSheet(null)} />}
    </div>
  )
}
