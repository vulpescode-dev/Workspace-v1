import type { UserSummary } from '@/features/accounts/types'
import type { Article } from '@/features/blog/api/blog.api'
import type { DocumentItem } from '@/features/documents/api/documents.api'
import type { FormSummary } from '@/features/forms/api/forms.api'
import type { Ticket } from '@/features/helpdesk/api/helpdesk.api'
import type { Listing } from '@/features/marketplace/api/marketplace.api'
import type { DirectoryPerson } from '@/features/people/api/people.api'
import type { Post } from '@/features/posts/types'
import { api } from '@/lib/api/client'
import type { Paginated } from '@/types/api'

/** Cuántos resultados se muestran por sección (la paginación de cada API lo permite con `page_size`). */
export const RESULTS_PER_SECTION = 5

/** Un resultado ya listo para pintar, venga de la sección que venga. */
export interface SearchHit {
  key: string
  to: string
  title: string
  subtitle: string
  person?: UserSummary
}
export interface SearchSection {
  id: string
  label: string
  /** A dónde lleva «Ver todos» (la sección con la búsqueda puesta). Sin él, no hay página que liste todo. */
  all?: (q: string) => string
  fetch: (q: string) => Promise<{ count: number; hits: SearchHit[] }>
}

const get = <T,>(url: string, params: Record<string, unknown>) =>
  api.get<Paginated<T>>(url, { params: { ...params, page_size: RESULTS_PER_SECTION } }).then(({ data }) => data)
const enc = encodeURIComponent

/**
 * La búsqueda general consulta en paralelo las APIs de cada sección (todas ya filtran por texto y respetan
 * quién puede ver qué). Así no hace falta una API nueva; si un día pesa, se junta en una sola.
 */
export const SEARCH_SECTIONS: SearchSection[] = [
  {
    id: 'people', label: 'Personas', all: (q) => `/people?q=${enc(q)}`,
    fetch: (q) => get<DirectoryPerson>('/accounts/users/', { search: q }).then(({ count, results }) => ({
      count, hits: results.map((p) => ({ key: `p${p.id}`, to: `/profile/${p.id}`, title: p.name, subtitle: [p.job_title, p.department].filter(Boolean).join(' · '), person: p })),
    })),
  },
  {
    id: 'posts', label: 'Publicaciones',
    fetch: (q) => get<Post>('/social/posts/', { q }).then(({ count, results }) => ({
      count, hits: results.map((p) => ({ key: `s${p.id}`, to: `/posts/${p.id}`, title: p.body, subtitle: p.author.name, person: p.author })),
    })),
  },
  {
    id: 'documents', label: 'Documentos', all: (q) => `/documents?q=${enc(q)}`,
    fetch: (q) => get<DocumentItem>('/documents/documents/', { q }).then(({ count, results }) => ({
      count, hits: results.map((d) => ({ key: `d${d.id}`, to: `/documents/${d.id}`, title: d.title, subtitle: `${d.category.name} · ${d.owner.name}` })),
    })),
  },
  {
    id: 'blog', label: 'Noticias', all: (q) => `/blog?q=${enc(q)}`,
    fetch: (q) => get<Article>('/blog/articles/', { q }).then(({ count, results }) => ({
      count, hits: results.map((a) => ({ key: `n${a.id}`, to: `/blog/${a.id}`, title: a.title, subtitle: a.excerpt || a.author.name })),
    })),
  },
  {
    id: 'forms', label: 'Formularios', all: (q) => `/forms?view=all&q=${enc(q)}`,
    fetch: (q) => get<FormSummary>('/forms/forms/', { q }).then(({ count, results }) => ({
      count, hits: results.map((f) => ({ key: `f${f.uuid}`, to: `/forms/${f.uuid}`, title: f.title, subtitle: f.submitted ? 'Respondido' : f.accepting ? 'Abierto' : 'Cerrado' })),
    })),
  },
  {
    id: 'marketplace', label: 'Marketplace', all: (q) => `/marketplace?sold=1&q=${enc(q)}`,
    fetch: (q) => get<Listing>('/marketplace/listings/', { q }).then(({ count, results }) => ({
      count, hits: results.map((l) => ({ key: `m${l.id}`, to: `/marketplace/${l.id}`, title: l.title, subtitle: `${l.status === 'sold' ? 'Vendido · ' : ''}${l.seller.name}` })),
    })),
  },
  {
    id: 'helpdesk', label: 'Mesa de ayuda', all: (q) => `/helpdesk?status=all&q=${enc(q)}`,
    fetch: (q) => get<Ticket>('/helpdesk/tickets/', { q }).then(({ count, results }) => ({
      count, hits: results.map((t) => ({ key: `t${t.id}`, to: `/helpdesk/${t.id}`, title: `${t.folio} · ${t.title}`, subtitle: `${t.status_label} · ${t.department?.name ?? 'Sin clasificar'}` })),
    })),
  },
]
