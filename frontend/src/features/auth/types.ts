export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated'

export interface LoginCredentials {
  /** Usuario o correo (el backend acepta ambos en el mismo campo). */
  username: string
  password: string
}
