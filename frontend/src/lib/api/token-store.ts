/**
 * Access token en memoria (nunca en localStorage ni en cookies legibles por JS).
 * El refresh token vive en una cookie httpOnly que solo ve el backend (/api/auth/).
 */
type Listener = (token: string | null) => void

let accessToken: string | null = null
const listeners = new Set<Listener>()

export const tokenStore = {
  get: () => accessToken,
  set(token: string | null) {
    accessToken = token
    listeners.forEach((listener) => listener(token))
  },
  subscribe(listener: Listener) {
    listeners.add(listener)
    return () => listeners.delete(listener)
  },
}
