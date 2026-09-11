import { http } from '@/services/http'
import type { Paper } from './data'

export interface PaperCheckInput { title: string; doi?: string; arxiv_id?: string }
export interface PaperCheckResult { exists: boolean; paper_id?: number; status?: string }

export const papersApi = {
  list: () => http.get<Paper[]>('/papers/'),
  check: (input: PaperCheckInput) => http.post<PaperCheckResult>('/papers/check/', input),
  create: (paper: Partial<Paper>) => http.post<Paper>('/papers/', paper),
  export: (format: 'markdown' | 'json') => http.get('/papers/export/', { params: { format }, responseType: format === 'json' ? 'json' : 'text' }),
}

