import { api } from '@/lib/api/client'

import type { Paginated } from '@/types/api'

import type { Story, StoryGroup, StoryViewerEntry } from '../types'

export const storiesApi = {
  tray: () => api.get<StoryGroup[]>('/social/stories/').then(({ data }) => data),
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<Story>('/social/stories/', form).then(({ data }) => data)
  },
  markSeen: (id: number) => api.post(`/social/stories/${id}/seen/`),
  remove: (id: number) => api.delete(`/social/stories/${id}/`),
  viewers: (id: number, page: number) =>
    api.get<Paginated<StoryViewerEntry>>(`/social/stories/${id}/viewers/`, { params: { page } }).then(({ data }) => data),
}

export const storiesKeys = {
  all: ['stories'] as const,
  tray: () => [...storiesKeys.all, 'tray'] as const,
  viewers: (id: number) => [...storiesKeys.all, id, 'viewers'] as const,
}
