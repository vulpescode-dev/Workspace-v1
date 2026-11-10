import { Building2, File, FileImage, FileSpreadsheet, FileText, Globe, Presentation, Users } from 'lucide-react'

/** Tipo de archivo → ícono y color (como en un explorador de archivos): se reconoce de un vistazo. */
export function kindOf(contentType = '', name = '') {
  const ext = name.split('.').pop()?.toLowerCase() ?? ''
  if (contentType === 'application/pdf' || ext === 'pdf') return { icon: FileText, tone: 'bg-red-50 text-red-600', label: 'PDF' }
  if (contentType.includes('wordprocessing') || ext === 'docx') return { icon: FileText, tone: 'bg-blue-50 text-blue-600', label: 'Word' }
  if (contentType.includes('spreadsheet') || ext === 'xlsx' || ext === 'csv') return { icon: FileSpreadsheet, tone: 'bg-emerald-50 text-emerald-600', label: ext === 'csv' ? 'CSV' : 'Excel' }
  if (contentType.includes('presentation') || ext === 'pptx') return { icon: Presentation, tone: 'bg-orange-50 text-orange-600', label: 'PowerPoint' }
  if (contentType.startsWith('image/')) return { icon: FileImage, tone: 'bg-violet-50 text-violet-600', label: 'Imagen' }
  if (contentType.startsWith('text/')) return { icon: FileText, tone: 'bg-slate-100 text-slate-600', label: 'Texto' }
  return { icon: File, tone: 'bg-slate-100 text-slate-600', label: 'Archivo' }
}

export const fileKindLabel = (contentType?: string, name?: string) => kindOf(contentType, name).label

/** «1.2 MB», «340 KB». */
export function formatSize(bytes: number) {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${Math.max(1, Math.round(bytes / 1024))} KB`
}

/** Ícono de quién ve el documento. */
export const VISIBILITY_ICONS = { public: Globe, departments: Building2, users: Users }
