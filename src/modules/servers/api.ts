import { http } from '@/services/http'
import type { Server } from './data'

export type ServerAction = 'refresh_status' | 'start_container' | 'stop_container' | 'restart_container' | 'fetch_logs'

export interface ServerMetric { id: number; recordedAt: string; cpu: number; memory: { used: number; total: number }; disk: { used: number; total: number }; gpuUtilization: number | null; gpuCount: number; containers: number; loadAverage?: number | null }

export const serversApi = {
  remove: (id: number) => http.delete(`/servers/${id}/`),
  update: (id: number, value: Partial<Server> & { password?: string }) => http.patch<Server>(`/servers/${id}/`, value),
  list: () => http.get<Server[]>('/servers/'),
  status: (id: number) => http.get<Server>(`/servers/${id}/status/`),
  runAction: (id: number, action: ServerAction, payload: Record<string, unknown> = {}) => http.post(`/servers/${id}/actions/`, { action, ...payload }),
  testConnection: (id: number) => http.post<{ status: string; message: string; fingerprint?: string }>(`/servers/${id}/test-connection/`),
  trustHost: (id: number, fingerprint: string) => http.post<{ accepted: boolean; message: string; server: Server }>(`/servers/${id}/trust-host/`, { fingerprint }),
  metrics: (id: number, hours = 24, limit = 240) => http.get<{ serverId: number; hours: number; count: number; results: ServerMetric[] }>(`/servers/${id}/metrics/`, { params: { hours, limit } }),
}
