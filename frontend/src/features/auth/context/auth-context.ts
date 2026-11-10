import { createContext } from 'react'

import type { AuthStatus, LoginCredentials } from '../types'

export interface AuthContextValue {
  status: AuthStatus
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
