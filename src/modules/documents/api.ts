import { http } from '@/services/http'
import type { NoteKind, PublicNote } from './types'

export interface NoteListParams {
  kind?: NoteKind
  tag?: string
  search?: string
}

export const documentsApi = {
  listPublic: (params?: NoteListParams) => http.get<PublicNote[]>('/docs/', { params: { ...params, visibility: 'public' } }),
  getPublic: (slug: string) => http.get<PublicNote>(`/docs/${slug}/`),
}

