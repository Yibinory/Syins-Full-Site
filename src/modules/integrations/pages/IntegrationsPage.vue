<script setup lang="ts">
import { t } from '@/i18n'
import { onMounted, reactive, ref } from 'vue'
import { ExternalLink, PanelsTopLeft, Plus, Trash2 } from 'lucide-vue-next'
import DashboardPageHeader from '@/components/shared/DashboardPageHeader.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import { useIntegrationsStore } from '@/stores/integrations'
import type { EmbeddedPage } from '../api'

const store = useIntegrationsStore()
const editingSlug = ref<string | undefined>()
const showForm = ref(false)
const busy = ref(false)
const notice = ref('')
const draft = reactive<Partial<EmbeddedPage>>({ title: '', description: '', url: '', icon: '', order: 0, enabled: true, publiclyVisible: false, openInNewTab: true })

function reset() {
  editingSlug.value = undefined
  Object.assign(draft, { title: '', description: '', url: '', icon: '', order: store.pages.length, enabled: true, publiclyVisible: false, openInNewTab: true })
}

function edit(page: EmbeddedPage) {
  editingSlug.value = page.slug
  Object.assign(draft, page)
  showForm.value = true
  notice.value = ''
}

function newPage() {
  reset()
  showForm.value = true
  notice.value = ''
}

async function save() {
  if (!draft.title?.trim() || !draft.url?.trim()) { notice.value = 'Title and URL are required.'; return }
  busy.value = true
  try {
    await store.save({ ...draft, title: draft.title.trim(), url: draft.url.trim() }, editingSlug.value)
    notice.value = editingSlug.value ? 'Dashboard page updated.' : 'Dashboard page added.'
    showForm.value = false
    reset()
  } catch { notice.value = 'The dashboard page could not be saved. Check that the URL uses http:// or https://.' }
  finally { busy.value = false }
}

async function remove(page: EmbeddedPage) {
  if (!window.confirm(t('Remove this dashboard page?'))) return
  try { await store.remove(page.slug); notice.value = 'Dashboard page removed.' }
  catch { notice.value = 'The dashboard page could not be removed.' }
}

onMounted(() => store.hydrate())
</script>

<template>
  <div>
    <DashboardPageHeader :title="$t('Dashboard pages')" :description="$t('Add useful internal tools such as 3x-ui without leaving the research workspace.')">
      <AppButton @click="newPage"><Plus :size="15" /> {{ $t("Add page") }}</AppButton>
    </DashboardPageHeader>
    <p v-if="notice" class="feedback" role="status">{{ $t(notice) }}</p>
    <form v-if="showForm" class="record-editor integration-editor" @submit.prevent="save">
      <div class="editor-heading"><h2>{{ editingSlug ? $t('Edit dashboard page') : $t('Add dashboard page') }}</h2><AppButton type="submit" :disabled="busy">{{ busy ? $t('Saving…') : $t('Save page') }}</AppButton></div>
      <div class="field-grid"><label>{{ $t("Title") }}<input v-model="draft.title" required :placeholder="$t('3x-ui')" /></label><label>{{ $t("URL") }}<input v-model="draft.url" type="url" required :placeholder="$t('https://panel.example.com/')" /></label><label>{{ $t("Short description") }}<input v-model="draft.description" :placeholder="$t('Proxy management panel')" /></label><label>{{ $t("Icon label") }}<input v-model="draft.icon" :placeholder="$t('XUI')" /></label><label>{{ $t("Display order") }}<input v-model.number="draft.order" type="number" min="0" /></label></div>
      <label class="check-field"><input v-model="draft.enabled" type="checkbox" /> {{ $t("Show this page in the dashboard") }}</label>
      <label class="check-field"><input v-model="draft.publiclyVisible" type="checkbox" /> {{ $t("Show on the public tools page") }}</label>
      <p class="muted-copy">{{ $t("Published pages expose their URL to visitors. Keep private admin panels hidden unless you intend to share them.") }}</p>
      <label class="check-field"><input v-model="draft.openInNewTab" type="checkbox" /> {{ $t("Offer an external-tab link") }}</label>
      <div class="editor-actions"><AppButton type="submit" :disabled="busy">{{ $t("Save page") }}</AppButton><button type="button" @click="showForm = false">{{ $t("Cancel") }}</button></div>
      <p class="muted-copy">{{ $t("Some external services intentionally block iframe embedding with X-Frame-Options or Content-Security-Policy. The external link remains available when that happens.") }}</p>
    </form>
    <section class="integration-list">
      <article v-for="page in store.pages" :key="page.id" class="integration-row">
        <div class="integration-icon"><PanelsTopLeft :size="17" /></div>
        <div><h2>{{ page.title }}</h2><p>{{ page.description || page.url }}</p><small>{{ page.url }}</small></div>
        <div class="integration-row-badges"><AppBadge :tone="page.enabled ? 'success' : 'neutral'">{{ page.enabled ? $t('Enabled') : $t('Hidden') }}</AppBadge>
        <AppBadge v-if="page.publiclyVisible" tone="info">{{ $t("Public") }}</AppBadge></div>
        <div class="integration-row-actions"><RouterLink :to="'/dashboard/integrations/' + page.slug">{{ $t("Open") }} <ExternalLink :size="13" /></RouterLink><button type="button" @click="edit(page)">{{ $t("Edit") }}</button><button type="button" class="danger" @click="remove(page)"><Trash2 :size="14" /></button></div>
      </article>
      <div v-if="!store.pages.length" class="module-placeholder"><div><PanelsTopLeft :size="28" /><h2>{{ $t("No dashboard pages yet") }}</h2><p>{{ $t("Add a URL to keep an external research service next to your papers, notes and servers.") }}</p><AppButton @click="newPage">{{ $t("Add the first page") }}</AppButton></div></div>
    </section>
  </div>
</template>
