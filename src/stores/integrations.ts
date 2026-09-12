import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listData } from '@/services/api'
import { integrationsApi, type EmbeddedPage } from '@/modules/integrations/api'

export const useIntegrationsStore = defineStore('integrations', () => {
  const pages = ref<EmbeddedPage[]>([])
  const hydrated = ref(false)

  async function hydrate(force = false) {
    if (hydrated.value && !force) return
    try {
      const response = await integrationsApi.list()
      pages.value = listData<EmbeddedPage>(response.data)
      hydrated.value = true
    } catch {
      // The dashboard can still render the manager when the integrations endpoint is unavailable.
    }
  }

  async function save(page: Partial<EmbeddedPage>, existingSlug?: string) {
    const response = existingSlug ? await integrationsApi.update(existingSlug, page) : await integrationsApi.create(page)
    const index = pages.value.findIndex(item => item.slug === existingSlug || item.slug === response.data.slug)
    if (index === -1) pages.value.push(response.data)
    else pages.value[index] = response.data
    pages.value.sort((a, b) => a.order - b.order || a.title.localeCompare(b.title))
    return response.data
  }

  async function remove(slug: string) {
    await integrationsApi.remove(slug)
    pages.value = pages.value.filter(page => page.slug !== slug)
  }

  return { pages, hydrated, hydrate, save, remove }
})
