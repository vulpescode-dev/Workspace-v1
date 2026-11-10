import { useEffect } from 'react'

import { env } from '@/config/env'

/** Título de la pestaña: «Sección · Proyecto». */
export function useDocumentTitle(title?: string) {
  useEffect(() => {
    document.title = title ? `${title} · ${env.projectName}` : env.projectName
  }, [title])
}
