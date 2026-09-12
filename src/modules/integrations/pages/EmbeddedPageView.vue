<script setup lang="ts">
import { ref, watch } from 'vue'
import { ArrowLeft, ExternalLink, Home, RotateCw } from 'lucide-vue-next'
import { useRoute } from 'vue-router'
import DashboardPageHeader from '@/components/shared/DashboardPageHeader.vue'
import AppButton from '@/components/ui/AppButton.vue'
import { integrationsApi, type EmbeddedPage } from '../api'

const route = useRoute()
const page = ref<EmbeddedPage | null>(null)
const loading = ref(true)
const error = ref('')
const frameKey = ref(0)
const frameUrl = ref('')
const address = ref('')

// Only change src on an explicit navigation, never in response to a frame load.
// Cross-origin frames own their internal history; their current URL cannot be read.
watch(() => route.params.slug, async (slug, _, onCleanup) => {
  let active = true
  onCleanup(() => { active = false })
  loading.value = true
  page.value = null
  error.value = ''
  try {
    const result = await integrationsApi.get(String(slug))
    if (!active) return
    page.value = result.data
    frameUrl.value = address.value = result.data.url
    frameKey.value++
  } catch { if (active) error.value = 'This dashboard page could not be loaded.' }
  finally { if (active) loading.value = false }
}, { immediate: true })

function navigate(url = address.value) {
  try {
    const target = new URL(url)
    if (!['http:', 'https:'].includes(target.protocol) || target.username || target.password) throw new Error()
    frameUrl.value = address.value = target.href
    frameKey.value++
    error.value = ''
  } catch { error.value = 'Enter a complete http or https URL without credentials.' }
}
</script>

<template>
  <div>
    <DashboardPageHeader v-if="page" :title="page.title" :description="page.description">
      <RouterLink class="dashboard-preview-link" to="/dashboard/integrations"><ArrowLeft :size="15" /> {{ $t("All dashboard pages") }}</RouterLink>
      <a class="dashboard-preview-link" :href="frameUrl" target="_blank" rel="noopener noreferrer">{{ $t("Open in browser") }} <ExternalLink :size="14" /></a>
    </DashboardPageHeader>
    <p v-if="loading" class="feedback">{{ $t("Loading external page…") }}</p>
    <p v-if="error" class="feedback" role="alert">{{ $t(error) }}</p>
    <section v-if="page && !loading" class="embedded-page-frame">
      <form class="embedded-page-toolbar" @submit.prevent="navigate()">
        <button type="button" :title="$t('Return to configured start page')" :aria-label="$t('Return to start page')" @click="navigate(page.url)"><Home :size="16" /></button>
        <button type="button" :title="$t('Reload entered URL')" :aria-label="$t('Reload entered URL')" @click="navigate(frameUrl)"><RotateCw :size="16" /></button>
        <input v-model="address" :aria-label="$t('URL to open in frame')" type="url" required />
        <AppButton type="submit" variant="secondary">{{ $t("Go") }}</AppButton>
      </form>
      <p class="embedded-page-notice">{{ $t("Navigate inside the page as usual. This bar shows the last URL entered, not the frame’s current address. Links that require a full browser may open a new tab or leave the dashboard.") }}</p>
      <iframe :key="frameKey" :src="frameUrl" :title="page.title" sandbox="allow-forms allow-modals allow-popups allow-popups-to-escape-sandbox allow-top-navigation-by-user-activation allow-downloads allow-scripts allow-same-origin" referrerpolicy="no-referrer" />
    </section>
  </div>
</template>
