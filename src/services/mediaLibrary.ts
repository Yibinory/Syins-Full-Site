import { http } from './http'

export interface MediaAsset {
  id: string
  name: string
  size: number
  createdAt: string
  kind: 'image' | 'video' | 'interactive'
  source: Blob
  rendered: Blob
  sourceUrl?: string
  renderedUrl?: string
  contentType?: string
}
const DB_NAME = 'research-os-media'
function database(): Promise<IDBDatabase> { return new Promise((resolve, reject) => { const req = indexedDB.open(DB_NAME, 1); req.onupgradeneeded = () => req.result.createObjectStore('assets', { keyPath: 'id' }); req.onsuccess = () => resolve(req.result); req.onerror = () => reject(req.error) }) }
async function operation<T>(mode: IDBTransactionMode, fn: (store: IDBObjectStore) => IDBRequest<T>): Promise<T> { const db = await database(); return new Promise((resolve, reject) => { const tx = db.transaction('assets', mode); const request = fn(tx.objectStore('assets')); tx.oncomplete = () => { db.close(); resolve(request.result) }; tx.onerror = () => { db.close(); reject(tx.error || request.error) }; tx.onabort = () => { db.close(); reject(tx.error || request.error) } }) }
function authenticatedBrowser() { return typeof window !== 'undefined' && localStorage.getItem('research-os:backend-auth') === 'true' }

export async function getMedia(id: string): Promise<MediaAsset | undefined> {
  const local = await operation<MediaAsset | undefined>('readonly', s => s.get(id))
  if (local) return local
  if (!authenticatedBrowser()) return undefined
  try {
    const { data } = await http.get<{ id: string; name: string; size: number; createdAt: string; kind: MediaAsset['kind']; contentType?: string; sourceUrl: string; renderedUrl?: string }>(`/media/${id}/`)
    const response = await fetch(data.sourceUrl)
    const blob = await response.blob()
    return { id: data.id, name: data.name, size: data.size, createdAt: data.createdAt, kind: data.kind, contentType: data.contentType, source: blob, rendered: blob, sourceUrl: data.sourceUrl, renderedUrl: data.renderedUrl || data.sourceUrl }
  } catch {
    return undefined
  }
}

export async function listMedia(): Promise<MediaAsset[]> {
  if (authenticatedBrowser()) {
    try {
      const { data } = await http.get<{ results?: Array<{ id: string; name: string; size: number; createdAt: string; kind: MediaAsset['kind']; contentType?: string; sourceUrl: string; renderedUrl?: string }> } | Array<{ id: string; name: string; size: number; createdAt: string; kind: MediaAsset['kind']; contentType?: string; sourceUrl: string; renderedUrl?: string }>>('/media/?page_size=200')
      const values = Array.isArray(data) ? data : data.results || []
      return values.map(item => ({ id: item.id, name: item.name, size: item.size, createdAt: item.createdAt, kind: item.kind, contentType: item.contentType, source: new Blob(), rendered: new Blob(), sourceUrl: item.sourceUrl, renderedUrl: item.renderedUrl || item.sourceUrl }))
    } catch { /* use local assets below */ }
  }
  return operation<MediaAsset[]>('readonly', s => s.getAll())
}

export const putMedia = (asset: MediaAsset) => operation('readwrite', s => s.put(asset))
export async function deleteMedia(id: string) {
  let deletedLocal = false
  try { await operation('readwrite', s => s.delete(id)); deletedLocal = true } catch { /* remote asset */ }
  if (authenticatedBrowser()) {
    try { await http.delete(`/media/${id}/`) } catch { if (!deletedLocal) throw new Error('The file could not be deleted.') }
  }
}
export async function importMedia(file: File): Promise<MediaAsset> {
  if (file.size > 25 * 1024 * 1024) throw new Error('File exceeds the 25 MB limit.')
  if (authenticatedBrowser()) {
    try {
      const form = new FormData()
      form.append('upload', file)
      const { data } = await http.post<{ id: string; name: string; size: number; createdAt: string; kind: MediaAsset['kind']; contentType?: string; sourceUrl: string; renderedUrl?: string }>('/media/', form, { headers: { 'Content-Type': 'multipart/form-data' } })
      return { id: data.id, name: data.name, size: data.size, createdAt: data.createdAt, kind: data.kind, contentType: data.contentType, source: file, rendered: file, sourceUrl: data.sourceUrl, renderedUrl: data.renderedUrl || data.sourceUrl }
    } catch (error) {
      const message = error instanceof Error ? error.message : ''
      if (message && !/network|failed to fetch|request failed|timeout/i.test(message)) throw error
      // When the backend is temporarily unavailable, retain the local import path.
    }
  }
  const ext = file.name.split('.').pop()?.toLowerCase()
  let kind: MediaAsset['kind']; let rendered: Blob
  if (['html', 'htm', 'vue', 'zip'].includes(ext || '')) { kind = 'interactive'; const { compileInteractive } = await import('./interactiveCompiler'); rendered = new Blob([await compileInteractive(file)], { type: 'text/html' }) }
  else if (['png', 'jpg', 'jpeg', 'webp', 'svg', 'gif', 'avif'].includes(ext || '')) { kind = 'image'; rendered = file }
  else if (['mp4', 'webm'].includes(ext || '')) { kind = 'video'; rendered = file }
  else throw new Error('Choose an image, MP4/WebM, HTML, Vue component, or ZIP archive.')
  const asset = { id: crypto.randomUUID(), name: file.name, size: file.size, createdAt: new Date().toISOString(), kind, source: file, rendered }
  await putMedia(asset)
  return asset
}
