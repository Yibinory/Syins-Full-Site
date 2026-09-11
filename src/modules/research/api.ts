import { http } from '@/services/http'
import type { ResearchProject } from './data'

export const researchApi = {
  listProjects: () => http.get<ResearchProject[]>('/research/projects/'),
  getProject: (slug: string) => http.get<ResearchProject>(`/research/projects/${slug}/`),
}

