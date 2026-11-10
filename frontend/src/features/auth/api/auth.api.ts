import { api } from '@/lib/api/client'

import type { LoginCredentials } from '../types'

/** `/api/auth/`: el refresh token nunca pasa por JavaScript, solo por la cookie httpOnly. */
export const authApi = {
  login: (credentials: LoginCredentials) =>
    api.post<{ access: string }>('/auth/login/', credentials).then(({ data }) => data.access),
  logout: () => api.post('/auth/logout/'),
}
