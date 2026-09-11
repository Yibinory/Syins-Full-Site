import { http } from '@/services/http'
import type { Publication } from './data'

export const publicationsApi = {
  list: () => http.get<Publication[]>('/publications/'),
  get: (slug: string) => http.get<Publication>(`/publications/${slug}/`),
}

