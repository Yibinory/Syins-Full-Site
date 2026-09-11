import { http } from '@/services/http'
import type { Server } from './data'

export type ServerAction = 'refresh_status' | 'start_container' | 'stop_container' | 'restart_container' | 'fetch_logs'

export const serversApi = {
  list: () => http.get<Server[]>('/servers/'),
  status: (id: number) => http.get<Server>(`/servers/${id}/status/`),
  runAction: (id: number, action: ServerAction, payload: Record<string, unknown> = {}) => http.post(`/servers/${id}/actions/`, { action, ...payload }),
}

