import { api } from '@/lib/api/client'

import type { Birthday, Profile } from '../types'

export const accountsApi = {
  me: () => api.get<Profile>('/accounts/me/').then(({ data }) => data),
  birthdays: () => api.get<Birthday[]>('/accounts/birthdays/').then(({ data }) => data),
}
