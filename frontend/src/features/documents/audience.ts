import type { UserSummary } from '@/features/accounts/types'

import type { Visibility } from './api/documents.api'

/** «Quién lo ve» mientras se edita: departamentos por id, personas con su foto y nombre (para los chips). */
export interface Audience { visibility: Visibility; departments: number[]; people: UserSummary[] }

/** Revisa que «Departamentos» o «Personas» tengan a alguien elegido. Devuelve el error o `null`. */
export function audienceError({ visibility, departments, people }: Audience) {
  if (visibility === 'departments' && departments.length === 0) return 'Elige al menos un departamento.'
  if (visibility === 'users' && people.length === 0) return 'Elige al menos una persona.'
  return null
}

/** Agrega la audiencia a un FormData (subida multipart). */
export function appendAudience(form: FormData, { visibility, departments, people }: Audience) {
  form.append('visibility', visibility)
  if (visibility === 'departments') departments.forEach((id) => form.append('departments', String(id)))
  if (visibility === 'users') people.forEach((person) => form.append('users', String(person.id)))
}
