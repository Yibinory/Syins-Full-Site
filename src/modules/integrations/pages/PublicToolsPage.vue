<script setup lang="ts">
import { useSiteContentStore } from '@/stores/siteContent'
const siteContent = useSiteContentStore()
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowUpRight, ArrowLeft } from 'lucide-vue-next'
import PublicLayout from '@/layouts/PublicLayout.vue'
import { listData } from '@/services/api'
import { integrationsApi, type EmbeddedPage } from '../api'
const route = useRoute()
const pages = ref<EmbeddedPage[]>([])
const selected = ref<EmbeddedPage | null>(null)
const loading = ref(true)
const error = ref('')
watch(() => route.params.slug, async (slug, _, cleanup) => {
  let active = true
  cleanup(() => { active = false })
  loading.value = true
  error.value = ''
  selected.value = null
  try {
    if (slug) {
      const response = await integrationsApi.publicGet(String(slug))
      if (active) selected.value = response.data
    } else {
      const response = await integrationsApi.publicList()
      if (active) pages.value = listData(response.data)
    }
  } catch { if (active) error.value = 'This page is unavailable or no longer public.' }
  finally { if (active) loading.value = false }
}, { immediate: true })
</script>
<template>
  <PublicLayout>
    <header class="public-tools-intro page-grid">
      <p class="section-kicker">{{ $t("05 / Tools") }}</p>
      <h1>{{ selected ? selected.title : siteContent.localized.toolsHeading }}</h1>
      <p>{{ selected ? selected.description : siteContent.localized.toolsDescription }}</p>
    </header>
    <section class="public-tools-content page-grid">
      <p v-if="loading">{{ $t("Loading…") }}</p>
      <p v-else-if="error" role="alert">{{ $t(error) }} <RouterLink to="/tools">{{ $t("All tools") }}</RouterLink></p>
      <template v-else-if="selected">
        <div class="public-tool-actions"><RouterLink to="/tools"><ArrowLeft :size="15" /> {{ $t("All tools") }}</RouterLink><a :href="selected.url" target="_blank" rel="noopener noreferrer">{{ $t("Open in browser") }} <ArrowUpRight :size="15" /></a></div>
        <iframe class="public-tool-frame" :key="selected.slug" :src="selected.url" :title="selected.title" sandbox="allow-forms allow-modals allow-popups allow-popups-to-escape-sandbox allow-top-navigation-by-user-activation allow-downloads allow-scripts allow-same-origin" referrerpolicy="no-referrer" />
        <p class="muted-copy">{{ $t("If this service does not allow embedding, use Open in browser.") }}</p>
      </template>
      <div v-else class="public-tool-list">
        <p v-if="!pages.length">{{ $t("No public tools yet.") }}</p>
        <RouterLink v-for="page in pages" :key="page.id" :to="'/tools/' + page.slug" class="public-tool-card">
          <span class="section-kicker">{{ page.icon || '↗' }}</span><h2>{{ page.title }}</h2><p>{{ page.description }}</p><span class="public-tool-open">{{ $t("Open tool") }} <ArrowUpRight :size="16" /></span>
        </RouterLink>
      </div>
    </section>
  </PublicLayout>
</template>
