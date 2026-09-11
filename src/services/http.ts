type ResponseType = 'json' | 'text' | 'blob'
export interface HttpConfig {
  headers?: Record<string, string>
  params?: Record<string, string | number | boolean | undefined>
  responseType?: ResponseType
}
export interface HttpResponse<T> {
  data: T
  status: number
  headers: Headers
}

const runtimeEnv = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env
const apiBase = runtimeEnv?.VITE_API_BASE_URL ?? '/api/v1'

function endpoint(path: string, params?: HttpConfig['params']) {
  const url = path.startsWith('http://') || path.startsWith('https://')
    ? new URL(path)
    : `${apiBase.replace(/\/$/, '')}/${path.replace(/^\//, '')}`
  if (params) {
    const search = url instanceof URL ? url.searchParams : new URLSearchParams()
    for (const [key, value] of Object.entries(params)) if (value !== undefined) search.set(key, String(value))
    if (url instanceof URL) return url.toString()
    const query = search.toString()
    return query ? `${url}?${query}` : url
  }
  return url.toString()
}

function csrfToken() {
  if (typeof document === 'undefined') return undefined
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : undefined
}

async function request<T>(method: string, path: string, body?: unknown, config: HttpConfig = {}): Promise<HttpResponse<T>> {
  const headers = new Headers({ Accept: 'application/json', ...(config.headers ?? {}) })
  const csrf = csrfToken()
  if (csrf) headers.set('X-CSRFToken', csrf)
  let payload: BodyInit | undefined
  if (body instanceof FormData || body instanceof Blob || typeof body === 'string') {
    payload = body
    if (body instanceof FormData) headers.delete('Content-Type')
  } else if (body !== undefined) {
    headers.set('Content-Type', 'application/json')
    payload = JSON.stringify(body)
  }
  const response = await fetch(endpoint(path, config.params), { method, headers, body: payload, credentials: 'include' })
  let data: unknown
  if (config.responseType === 'blob') data = await response.blob()
  else {
    const text = await response.text()
    data = text
    if (config.responseType !== 'text' && text) {
      try { data = JSON.parse(text) } catch { data = text }
    }
  }
  if (!response.ok) {
    const error = new Error(typeof data === 'string' ? data : `Request failed with status ${response.status}`) as Error & { response?: HttpResponse<unknown> }
    error.response = { data, status: response.status, headers: response.headers }
    throw error
  }
  return { data: data as T, status: response.status, headers: response.headers }
}

export const http = {
  get<T = unknown>(path: string, config?: HttpConfig) { return request<T>('GET', path, undefined, config) },
  post<T = unknown>(path: string, body?: unknown, config?: HttpConfig) { return request<T>('POST', path, body, config) },
  put<T = unknown>(path: string, body?: unknown, config?: HttpConfig) { return request<T>('PUT', path, body, config) },
  patch<T = unknown>(path: string, body?: unknown, config?: HttpConfig) { return request<T>('PATCH', path, body, config) },
  delete<T = unknown>(path: string, config?: HttpConfig) { return request<T>('DELETE', path, undefined, config) },
}
