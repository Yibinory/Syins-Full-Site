import { http } from '@/services/http'
import type { Paper } from './data'

export interface PaperCheckInput { title: string; doi?: string; arxiv_id?: string; arxivId?: string; excludeId?: number }
export interface PaperCheckResult { exists: boolean; paper_id?: number; status?: string; field?: string }

export interface PublicPaperNote {
  id: number
  slug: string
  title: string
  summary: string
  excerpt: string
  kind: string
  publishedAt: string | null
  readingTime: string
  visibility: 'private' | 'public' | 'unlisted'
  tags: string[]
  requiresAuth: boolean
}

export interface PublicPaper extends Paper {
  notes: PublicPaperNote[]
  publiclyVisible: boolean
}

export const papersApi = {
  list: () => http.get<Paper[] | { results?: Paper[] }>('/papers/'),
  check: (input: PaperCheckInput) => http.post<PaperCheckResult>('/papers/check/', input),
  create: (paper: Partial<Paper>) => http.post<Paper>('/papers/', paper),
  publicList: (params?: { search?: string; tag?: string; ordering?: string }) => http.get<PublicPaper[] | { results?: PublicPaper[] }>('/public/papers/', { params: { ...params, page_size: 100, ordering: params?.ordering ?? '-recommended_at' } }),
  publicGet: (id: number) => http.get<PublicPaper>(`/public/papers/${id}/`),
  export: (format: 'markdown' | 'json') => http.get('/papers/export/', { params: { format }, responseType: format === 'json' ? 'json' : 'text' }),
}
