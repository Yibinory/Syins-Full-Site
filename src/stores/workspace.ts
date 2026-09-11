import { defineStore } from 'pinia'
import { ref } from 'vue'
import { http } from '@/services/http'
import { listData, localStorageJson, saveLocalStorageJson } from '@/services/api'
import { useAuthStore } from './auth'
import { papers as paperSeeds, type Paper } from '@/modules/papers/data'
import { publications as publicationSeeds, type Publication } from '@/modules/publications/data'
import { publicNotes } from '@/modules/documents/data'
import type { PublicNote, NoteKind } from '@/modules/documents/types'
import type { Server } from '@/modules/servers/data'

export interface ManagedPaper extends Paper { noteIds: number[]; paperUrl: string }
export interface ManagedPublication extends Publication {
  slug?: string
  motivation: string
  approach: string
  abstract: string
  paperUrl: string
  codeUrl: string
  projectUrl: string
  bibtex: string
  mediaType: 'image' | 'video' | 'interactive'
  mediaUrl: string
  mediaAlt: string
  caption: string
  mediaAssetId?: string
}
export interface Document extends PublicNote {
  content: string
  visibility: 'private' | 'public' | 'unlisted'
  updatedAt: string
  trashedAt: string | null
}
export interface WorkspaceSettings {
  defaultNoteVisibility: Document['visibility']
  defaultNoteKind: NoteKind
  pageSize: number
  siteTitle: string
  updatedAt?: string
}

export const normalizeTags = (tags: string[]) => [...new Map(tags.map(t => t.trim()).filter(Boolean).map(t => [t.toLowerCase(), t])).values()]
export const newId = () => Date.now() + Math.floor(Math.random() * 1000)
export const today = () => new Date().toISOString().slice(0, 10)

const seededPapers = paperSeeds.map(p => ({ ...structuredClone(p), noteIds: [], paperUrl: p.arxivId ? `https://arxiv.org/abs/${p.arxivId}` : '' }))
const seededPublications = publicationSeeds.map(p => ({ ...structuredClone(p), slug: undefined, motivation: '', approach: '', abstract: '', paperUrl: '', codeUrl: '', projectUrl: '', bibtex: '', mediaType: 'image' as const, mediaUrl: p.image || '', mediaAlt: p.title, caption: '', mediaAssetId: undefined }))
const seededDocuments = publicNotes.map(n => ({ ...structuredClone(n), content: `# ${n.title}\n\n${n.excerpt}`, visibility: 'public' as const, updatedAt: n.publishedAt, trashedAt: null }))
const defaultSettings: WorkspaceSettings = { defaultNoteVisibility: 'private', defaultNoteKind: 'Research Note', pageSize: 20, siteTitle: 'Research OS' }

function replaceRecord<T extends { id: number }>(records: T[], value: T) {
  const index = records.findIndex(item => item.id === value.id)
  if (index < 0) records.unshift(value)
  else records[index] = value
}

export const useWorkspaceStore = defineStore('workspace', () => {
  const papers = ref<ManagedPaper[]>(localStorageJson('research-os:papers', structuredClone(seededPapers)))
  const publications = ref<ManagedPublication[]>(localStorageJson('research-os:publications', structuredClone(seededPublications)))
  const documents = ref<Document[]>(localStorageJson('research-os:documents', structuredClone(seededDocuments)))
  const servers = ref<Server[]>([])
  const settings = ref<WorkspaceSettings>(localStorageJson('research-os:preferences', structuredClone(defaultSettings)))
  const hydrated = ref(false)
  const offline = ref(false)

  function persistFallback() {
    saveLocalStorageJson('research-os:papers', papers.value)
    saveLocalStorageJson('research-os:publications', publications.value)
    saveLocalStorageJson('research-os:documents', documents.value)
    saveLocalStorageJson('research-os:preferences', settings.value)
  }

  async function hydrate() {
    if (hydrated.value) return
    const auth = useAuthStore()
    try {
      const publicResponses = await Promise.all([
        http.get<ManagedPublication[] | { results?: ManagedPublication[] }>('/publications/?page_size=200'),
        http.get<Document[] | { results?: Document[] }>('/docs/?visibility=public&page_size=200'),
      ])
      publications.value = listData<ManagedPublication>(publicResponses[0].data)
      documents.value = listData<Document>(publicResponses[1].data)
      if (auth.isAuthenticated) {
        const privateResponses = await Promise.all([
          http.get<ManagedPaper[] | { results?: ManagedPaper[] }>('/papers/?page_size=200'),
          http.get<Document[] | { results?: Document[] }>('/docs/?page_size=200'),
          http.get<Document[] | { results?: Document[] }>('/docs/?trash=1&page_size=200'),
          http.get<Server[] | { results?: Server[] }>('/servers/?page_size=200'),
          http.get<WorkspaceSettings>('/settings/'),
        ])
        papers.value = listData<ManagedPaper>(privateResponses[0].data)
        const activeDocuments = listData<Document>(privateResponses[1].data)
        const trashedDocuments = listData<Document>(privateResponses[2].data)
        documents.value = [...activeDocuments, ...trashedDocuments.filter((trash) => !activeDocuments.some((active) => active.id === trash.id))]
        servers.value = listData<Server>(privateResponses[3].data)
        settings.value = privateResponses[4].data
      } else {
        papers.value = []
        servers.value = []
      }
    } catch {
      offline.value = true
      // The old browser records remain a useful migration fallback if the API is not running yet.
    } finally {
      hydrated.value = true
    }
  }

  async function savePublication(value: ManagedPublication) {
    const existing = publications.value.find(item => item.id === value.id)
    replaceRecord(publications.value, value)
    try {
      const response = existing
        ? await http.put<ManagedPublication>(`/publications/${existing.slug}/`, value)
        : await http.post<ManagedPublication>('/publications/', value)
      if (!existing) publications.value = publications.value.filter(item => item.id !== value.id)
      replaceRecord(publications.value, response.data)
      return response.data
    } catch {
      replaceRecord(publications.value, value)
      persistFallback()
      return value
    }
  }

  async function deletePublication(value: ManagedPublication) {
    const existing = publications.value.find(item => item.id === value.id)
    try { if (existing?.slug) await http.delete(`/publications/${existing.slug}/`) } catch { /* keep local fallback usable */ }
    publications.value = publications.value.filter(item => item.id !== value.id)
    persistFallback()
  }

  async function createPaper(value: ManagedPaper) {
    papers.value.unshift(value)
    try {
      const response = await http.post<ManagedPaper>('/papers/', value)
      papers.value = papers.value.filter(item => item.id !== value.id)
      papers.value.unshift(response.data)
      return response.data
    } catch {
      persistFallback()
      return value
    }
  }

  async function updatePaper(value: ManagedPaper) {
    try {
      const response = await http.patch<ManagedPaper>(`/papers/${value.id}/`, value)
      const current = papers.value.find(item => item.id === value.id)
      if (current) Object.assign(current, response.data)
      else papers.value.unshift(response.data)
      return response.data
    } catch {
      persistFallback()
      return value
    }
  }

  async function saveDocument(value: Document) {
    const normalized = structuredClone(value)
    normalized.tags = normalizeTags(normalized.tags)
    normalized.updatedAt = today()
    normalized.displayDate = normalized.publishedAt
    normalized.excerpt = normalized.summary
    normalized.readingTime = `${Math.max(1, Math.ceil(normalized.content.length / 1000))} min`
    const existing = documents.value.find(item => item.id === normalized.id)
    replaceRecord(documents.value, normalized)
    try {
      const response = existing
        ? await http.put<Document>(`/docs/${existing.slug}/`, normalized)
        : await http.post<Document>('/docs/', normalized)
      if (!existing) documents.value = documents.value.filter(item => item.id !== normalized.id)
      replaceRecord(documents.value, response.data)
      return response.data
    } catch {
      persistFallback()
      return normalized
    }
  }

  async function linkNote(paperId: number, noteId: number, linked: boolean) {
    const paper = papers.value.find(item => item.id === paperId)
    if (!paper) return
    const note = documents.value.find(item => item.id === noteId)
    if (linked && (!note || note.trashedAt)) return
    paper.noteIds = linked ? [...new Set([...paper.noteIds, noteId])] : paper.noteIds.filter(id => id !== noteId)
    await updatePaper(paper)
  }

  async function trashDocument(id: number) {
    const doc = documents.value.find(item => item.id === id)
    if (!doc) return
    doc.trashedAt = new Date().toISOString()
    try {
      const response = await http.post<Document>(`/docs/${doc.slug}/trash/`)
      Object.assign(doc, response.data)
    } catch {
      persistFallback()
    }
  }

  async function restoreDocument(doc: Document) {
    doc.trashedAt = null
    try {
      const response = await http.post<Document>(`/docs/${doc.slug}/restore/`)
      Object.assign(doc, response.data)
    } catch {
      persistFallback()
    }
  }

  async function renameTag(from: string, to: string) {
    for (const item of [...papers.value, ...publications.value, ...documents.value]) item.tags = normalizeTags(item.tags.flatMap(tag => tag.toLowerCase() === from.toLowerCase() ? (to.trim() ? [to.trim()] : []) : [tag]))
    try { await http.post('/tags/rename/', { from, to }) } catch { /* local fallback below */ }
    persistFallback()
  }

  async function saveSettings() {
    try {
      const response = await http.patch<WorkspaceSettings>('/settings/', settings.value)
      settings.value = response.data
    } catch { persistFallback() }
  }

  async function refreshServers() {
    try {
      const response = await http.post<Server[] | { results?: Server[] }>('/servers/refresh/')
      servers.value = listData<Server>(response.data)
    } catch {
      // The dashboard keeps the last known snapshot when a connector is unavailable.
    }
    return servers.value
  }

  async function createServer(value: Partial<Server>) {
    try {
      const response = await http.post<Server>('/servers/', value)
      servers.value = [response.data, ...servers.value]
      return response.data
    } catch {
      return undefined
    }
  }

  return {
    papers, publications, documents, servers, settings, hydrated, offline,
    hydrate, savePublication, deletePublication, createPaper, updatePaper, saveDocument,
    linkNote, trashDocument, restoreDocument, renameTag, saveSettings, refreshServers, createServer,
  }
})
