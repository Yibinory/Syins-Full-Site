import { defineStore } from 'pinia'
import { ref } from 'vue'
import { profile } from '@/modules/profile/data'
import { http } from '@/services/http'
import { localStorageJson, saveLocalStorageJson } from '@/services/api'

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
  name: profile.name,
  title: 'Medical imaging researcher',
  location: profile.location,
  email: profile.email,
  headline: profile.headline,
  bio: profile.bio,
  researchDirections: 'Medical Image Processing × Domain Generalization × Image Generation',
  featuredResearchIntro: 'Exploring how medical images can be processed, generalized across domains, and generated.',
  selectedProjects: [
    { id: 'longitudinal', title: 'Longitudinal worlds of disease progression', motivation: 'Can a generative model learn plausible futures without losing the patient in the process?', approach: 'We investigate time-aware latent representations for synthesizing anatomically consistent follow-up images from incomplete clinical histories.', status: 'Active', mediaType: 'image', mediaUrl: '/images/longitudinal-mri-mock.png', mediaAlt: 'Illustrative longitudinal MRI sequence', caption: 'Illustrative placeholder · AI-generated imagery, not experimental results', links: [{ label: 'Project', url: '' }, { label: 'Preprint', url: '' }] },
    { id: 'generalization', title: 'Generalization beyond the hospital we know', motivation: 'What should a model remember when the scanner, protocol, and population all change?', approach: 'We study invariant anatomy and uncertain appearance across unseen domains in medical segmentation.', status: 'Ongoing', mediaType: 'image', mediaUrl: '/images/domain-generalization.svg', mediaAlt: 'Two source hospitals contribute to a shared model evaluated on an unseen hospital', caption: 'Conceptual illustration · Cross-hospital generalization', links: [{ label: 'Paper', url: '' }, { label: 'Code', url: '' }] },
  ],
  currentResearch: [
    { id: 1, number: '01', title: 'Medical Image Generation', text: 'Controllable generative models that preserve anatomy while exposing clinically meaningful variation.', status: 'Active', question: 'How can pathology change without silently changing patient identity?', method: 'Anatomy-conditioned diffusion · Counterfactual editing', updated: 'Updated 2 days ago' },
    { id: 2, number: '02', title: 'Longitudinal Image Modeling', text: 'Learning patient-specific trajectories to model disease progression across sparse clinical timepoints.', status: 'Exploring', question: 'What does a plausible future image look like when observations are sparse and irregular?', method: 'Temporal latent models · Calibrated uncertainty', updated: 'Updated today' },
    { id: 3, number: '03', title: 'Domain Generalization', text: 'Robust representations that transfer across scanners, institutions, and unseen acquisition protocols.', status: 'Active', question: 'Which visual features survive a change of hospital, scanner, and population?', method: 'Invariant representation learning · OOD evaluation', updated: 'Updated 5 days ago' },
  ],
  currentResearchHeading: 'Questions I’m working on now.',
  featuredResearchHeading: 'Images as evidence.',
  publicationsHeading: 'Selected papers and preprints.',
  publicationsDescription: 'Work on generalizable representation learning, longitudinal modeling, and controllable medical image generation.',
  notesHeading: 'Ideas in progress, organized to last.',
  notesDescription: 'Research notes, essays, practical guides, and living references—kept in one public library.',
  scholarUrl: '#',
  githubUrl: '#',
  cvUrl: '#',
}

export const useSiteContentStore = defineStore('site-content', () => {
  const persisted = localStorageJson<Partial<SiteContent>>('research-os:site-content', {})
  const content = ref<SiteContent>({
    ...structuredClone(defaults),
    ...persisted,
    selectedProjects: persisted.selectedProjects ?? structuredClone(defaults.selectedProjects),
    currentResearch: persisted.currentResearch ?? structuredClone(defaults.currentResearch),
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

  return { apiLoaded, content, lastSavedAt, hydrated, saving, hydrate, save, reset }
})
