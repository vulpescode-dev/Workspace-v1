/** Persona en forma corta (autor de un post, jefe directo…). */
export interface UserSummary {
  id: number
  name: string
  initials: string
  avatar_url: string
}

export interface FollowStats {
  followers_count: number
  following_count: number
  is_following: boolean
  follows_me: boolean
}

/** Perfil completo: `GET /api/accounts/me/` y `GET /api/accounts/users/:id/`. */
export interface Profile extends UserSummary {
  first_name: string
  email: string
  job_title: string
  department: string
  department_id: number | null
  manager: UserSummary | null
  bio: string
  date_joined: string
  /** Solo día y mes: el año (la edad) nunca sale del servidor. */
  birthday: { day: number; month: number } | null
  is_me: boolean
  posts_count: number
  follow: FollowStats
  /** Solo en mi propio perfil (`/me`): qué puedo hacer. Nunca viene en el perfil de otra persona. */
  access?: MyAccess
}

/** Mis permisos de negocio (`app.recurso.acción`). El superusuario puede todo sin importar la lista. */
export interface MyAccess {
  is_superuser: boolean
  permissions: string[]
}

/** `GET /api/accounts/birthdays/` — hoy y próximos 30 días, sin año. */
export interface Birthday extends UserSummary {
  job_title: string
  day: number
  month: number
  days_until: number
  is_today: boolean
}

/** Persona en listas con botón Seguir (sugerencias, seguidores). */
export interface Person extends UserSummary {
  job_title: string
  is_following: boolean
  is_me: boolean
}
