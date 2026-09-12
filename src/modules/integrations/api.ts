import { http } from '@/services/http'

export interface EmbeddedPage {
  id: number
  slug: string
  title: string
  description: string
  url: string
  icon: string
  order: number
  publiclyVisible: boolean
  enabled: boolean
  openInNewTab: boolean
  createdAt?: string
  updatedAt?: string
}

export const integrationsApi = {
  publicList: () => http.get<EmbeddedPage[] | { results?: EmbeddedPage[] }>('/public/pages/?page_size=200'),
  publicGet: (slug: string) => http.get<EmbeddedPage>(`/public/pages/${slug}/`),
  list: () => http.get<EmbeddedPage[] | { results?: EmbeddedPage[] }>('/integrations/pages/?ordering=order'),
  get: (slug: string) => http.get<EmbeddedPage>(`/integrations/pages/${slug}/`),
  create: (page: Partial<EmbeddedPage>) => http.post<EmbeddedPage>('/integrations/pages/', page),
  update: (slug: string, page: Partial<EmbeddedPage>) => http.patch<EmbeddedPage>(`/integrations/pages/${slug}/`, page),
  remove: (slug: string) => http.delete(`/integrations/pages/${slug}/`),
}
