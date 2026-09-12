import { http } from '@/services/http'
import type { NoteKind, PublicNote } from './types'

export interface NoteListParams {
  kind?: NoteKind
  tag?: string
  search?: string
}

export const documentsApi = {
  listPublic: (params?: NoteListParams) => http.get<PublicNote[] | { results?: PublicNote[] }>('/docs/', { params: { ...params, visibility: 'public' } }),
  getPublic: (slug: string) => http.get<PublicNote & { content?: string; visibility?: 'private' | 'public' | 'unlisted'; requiresAuth?: boolean }>(`/docs/${slug}/`),
  uploadMarkdown: (file: File, fields: Record<string, string | boolean | undefined> = {}) => {
    const form = new FormData()
    form.append('file', file)
    Object.entries(fields).forEach(([key, value]) => { if (value !== undefined) form.append(key, String(value)) })
    return http.post('/docs/upload/', form)
  },
}
