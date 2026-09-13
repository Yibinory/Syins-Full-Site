import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { locale, setLocale, hasSavedLocale } from '@/i18n'
import { resolveContent } from '@/services/localizedContent'
import { profile } from '@/modules/profile/data'
import { http } from '@/services/http'
import { saveLocalStorageJson } from '@/services/api'

export interface ResearchProject {
  id: string
  title: string
  motivation: string
  approach: string
  status: string
  mediaType: 'image' | 'video' | 'interactive'
  mediaAssetId?: string
  mediaUrl: string
  mediaAlt: string
  caption: string
  links: { label: string; url: string }[]
}

export interface SiteContent {
  defaultLanguage?: 'en' | 'zh'
  translations?: Record<string, Record<string, string>>
  papersHeading: string
  papersDescription: string
  toolsHeading: string
  toolsDescription: string
  name: string
  title: string
  location: string
  email: string
  headline: string
  bio: string
  researchDirections: string
  featuredResearchIntro: string
  selectedProjects: ResearchProject[]
  currentResearchHeading: string
  featuredResearchHeading: string
  publicationsHeading: string
  publicationsDescription: string
  notesHeading: string
  notesDescription: string
  scholarUrl: string
  githubUrl: string
  cvUrl: string
  currentResearch: Array<{
    id: number
    number: string
    title: string
    text: string
    status: string
    question: string
    method: string
    updated: string
  }>
}

const defaults: SiteContent = {
  papersHeading: 'Papers worth returning to.',
  papersDescription: 'A reading collection with recommendations, context, and linked notes.',
  toolsHeading: 'Tools & resources.',
  toolsDescription: 'A collection of useful external pages and research tools.',
  name: profile.name,
  title: 'Independent researcher',
  location: profile.location,
  email: profile.email,
  headline: profile.headline,
  bio: profile.bio,
  researchDirections: 'Research × Learning × Discovery',
  featuredResearchIntro: 'Projects and the questions behind them.',
  selectedProjects: [],
  currentResearch: [],
  currentResearchHeading: 'Questions I’m working on now.',
  featuredResearchHeading: 'Selected research.',
  publicationsHeading: 'Selected papers and preprints.',
  publicationsDescription: 'A growing collection of published work.',
  notesHeading: 'Ideas in progress, organized to last.',
  notesDescription: 'Research notes, essays, practical guides, and living references—kept in one public library.',
  scholarUrl: '#',
  githubUrl: '#',
  cvUrl: '#',
}

export const useSiteContentStore = defineStore('site-content', () => {
  const content = ref<SiteContent>({
    ...structuredClone(defaults),

    selectedProjects: [],
    currentResearch: [],
  })
  const lastSavedAt = ref(localStorage.getItem('research-os:site-content-saved-at') ?? '')
  const apiLoaded = ref(false)
  const hydrated = ref(false)
  const saving = ref(false)

  async function hydrate() {
    if (hydrated.value) return
    try {
      const response = await http.get<SiteContent>('/site/content/')
      content.value = response.data
      if (!hasSavedLocale) setLocale(response.data.defaultLanguage === 'zh' ? 'zh' : 'en')
      apiLoaded.value = true
      saveLocalStorageJson('research-os:site-content', content.value)
    } catch {
      // Keeping the last local draft makes the site usable while the API is temporarily offline.
    } finally {
      hydrated.value = true
    }
  }

  async function save() {
    saving.value = true
    try {
      const response = await http.put<SiteContent>('/site/content/', content.value)
      content.value = response.data
      lastSavedAt.value = new Date().toISOString()
      saveLocalStorageJson('research-os:site-content', content.value)
      localStorage.setItem('research-os:site-content-saved-at', lastSavedAt.value)
    } catch {
      lastSavedAt.value = new Date().toISOString()
      saveLocalStorageJson('research-os:site-content', content.value)
      localStorage.setItem('research-os:site-content-saved-at', lastSavedAt.value)
    } finally {
      saving.value = false
    }
  }

  async function reset() {
    content.value = structuredClone(defaults)
    await save()
  }

  const localized = computed(() => resolveContent(content.value, locale.value))

  return { localized, apiLoaded, content, lastSavedAt, hydrated, saving, hydrate, save, reset }
})
