/**
 * Qué permisos abren cada sección. Es el mismo criterio que el backend (`apps/accounts/api/permissions.py`):
 * entra quien tenga cualquiera de la lista (su `view` o algo que ya implique verla, como crear o atender).
 * Lo usan el menú (oculta lo que no puedes abrir) y el router (`RequireAccess`). El servidor vuelve a validar.
 */
export const SECTION_ACCESS = {
  people: ['accounts.users.view', 'accounts.users.view.all'],
  orgChart: ['org.chart.view'],
  posts: ['social.posts.view', 'social.posts.view.all', 'social.posts.create'],
  stories: ['social.stories.view', 'social.stories.create'],
  blog: ['blog.articles.view', 'blog.articles.view.all', 'blog.articles.create'],
  documents: ['documents.documents.view', 'documents.documents.view.all', 'documents.documents.create', 'documents.documents.manage'],
  forms: ['forms.forms.view', 'forms.forms.view.all', 'forms.forms.create'],
  helpdesk: ['helpdesk.tickets.view', 'helpdesk.tickets.view.all', 'helpdesk.tickets.create', 'helpdesk.tickets.attend'],
  marketplace: ['marketplace.listings.view', 'marketplace.listings.create'],
} as const satisfies Record<string, readonly string[]>

export type Section = keyof typeof SECTION_ACCESS

/** Lo que llega en `/me` → `access`. */
export interface AccessInfo {
  is_superuser: boolean
  permissions: string[]
}

/** La regla única: superusuario → sí; si no, el código debe estar en mis permisos. Sin datos aún → no. */
export function hasPermission(access: AccessInfo | null | undefined, codename: string): boolean {
  return Boolean(access && (access.is_superuser || access.permissions.includes(codename)))
}

/** ¿Abre esta sección? Basta con cualquiera de sus permisos (ver `SECTION_ACCESS`). */
export function canOpenSection(access: AccessInfo | null | undefined, section: Section): boolean {
  return SECTION_ACCESS[section].some((code) => hasPermission(access, code))
}
