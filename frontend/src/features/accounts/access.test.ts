import { describe, expect, it } from 'vitest'

import { canOpenSection, hasPermission, SECTION_ACCESS, type AccessInfo } from './access'

const user = (...permissions: string[]): AccessInfo => ({ is_superuser: false, permissions })
const superuser: AccessInfo = { is_superuser: true, permissions: [] }

describe('hasPermission', () => {
  it('sin datos todavía responde que no (mejor no mostrar un botón que luego desaparece)', () => {
    expect(hasPermission(undefined, 'social.posts.create')).toBe(false)
    expect(hasPermission(null, 'social.posts.create')).toBe(false)
  })

  it('solo con el código exacto', () => {
    const access = user('social.posts.view')
    expect(hasPermission(access, 'social.posts.view')).toBe(true)
    expect(hasPermission(access, 'social.posts.view.all')).toBe(false)
    expect(hasPermission(access, 'social.posts.create')).toBe(false)
  })

  it('el superusuario puede todo aunque no tenga roles', () => {
    expect(hasPermission(superuser, 'cualquier.cosa.inventada')).toBe(true)
  })
})

describe('canOpenSection', () => {
  it('se abre con su «view» o con algo que ya implique verla', () => {
    expect(canOpenSection(user('marketplace.listings.view'), 'marketplace')).toBe(true)
    expect(canOpenSection(user('marketplace.listings.create'), 'marketplace')).toBe(true)
    expect(canOpenSection(user('helpdesk.tickets.attend'), 'helpdesk')).toBe(true)
  })

  it('un permiso de otra sección no la abre', () => {
    expect(canOpenSection(user('blog.articles.view'), 'marketplace')).toBe(false)
    expect(canOpenSection(user(), 'people')).toBe(false)
  })

  it('el superusuario abre todas', () => {
    for (const section of Object.keys(SECTION_ACCESS) as (keyof typeof SECTION_ACCESS)[]) {
      expect(canOpenSection(superuser, section)).toBe(true)
    }
  })

  it('los códigos siguen el formato app.recurso.acción[.all]', () => {
    for (const codes of Object.values(SECTION_ACCESS)) {
      for (const code of codes) expect(code).toMatch(/^[a-z_]+\.[a-z_]+\.[a-z_]+(\.all)?$/)
    }
  })
})
