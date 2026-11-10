import { useCallback } from 'react'

import { canOpenSection, hasPermission, type Section } from '../access'
import { useMe } from './useMe'

/**
 * ¿Puedo hacer esto? Para mostrar u ocultar botones: `const can = useCan(); can('social.posts.create')`.
 * Regla: superusuario → sí, siempre; si no, el código debe estar en mis permisos (`/me` → `access`).
 * Mientras `/me` carga responde `false` (mejor no mostrar un botón que luego desaparece).
 * Solo es la interfaz: el servidor vuelve a validar cada acción.
 */
export function useCan() {
  const access = useMe().data?.access
  return useCallback(
    (codename: string) => hasPermission(access, codename),
    [access],
  )
}

/**
 * ¿Puedo abrir esta sección? `ready` = ya se sabe (llegó `/me`). Mientras no se sabe, `canSee` responde
 * `true`: el menú no parpadea quitando secciones y la página decide cuando llegue (`RequireAccess`).
 */
export function useSectionAccess() {
  const { data, isError } = useMe()
  const ready = Boolean(data) || isError
  const canSee = useCallback((section: Section) => !data || canOpenSection(data.access, section), [data])
  return { ready, canSee }
}
