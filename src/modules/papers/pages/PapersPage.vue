<script setup lang="ts">
import { computed, ref } from 'vue'
import { BookOpenText, Download, Plus, Search } from 'lucide-vue-next'
import DashboardPageHeader from '@/components/shared/DashboardPageHeader.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import PaperDrawer from '../components/PaperDrawer.vue'
import { paperStatusMeta, type PaperStatus } from '../data'
import { useWorkspaceStore, newId, today, type ManagedPaper } from '@/stores/workspace'
import { storeToRefs } from 'pinia'

const store = useWorkspaceStore()
const { papers } = storeToRefs(store)
type FilterValue = 'all' | PaperStatus
const tabs: { label: string; value: FilterValue }[] = [{ label: 'All', value: 'all' }, { label: 'To read', value: 'to_read' }, { label: 'Reading', value: 'reading' }, { label: 'Read', value: 'read' }, { label: 'Important', value: 'important' }]
const active = ref<FilterValue>('all')
const query = ref('')
const tagFilter = ref('')
const allTags = computed(() => [...new Set(papers.value.flatMap(p => p.tags))].sort())
const showAdd = ref(false)
const notice = ref('')
const busy = ref(false)
const newPaper = ref({ title: '', authors: '', venue: '', year: new Date().getFullYear(), topic: '', reason: '', abstract: '', paperUrl: '', doi: '', arxivId: '', publiclyVisible: false })
const selected = ref<ManagedPaper | null>(null)
const filtered = computed(() => papers.value.filter(paper => (active.value === 'all' || paper.status === active.value) && (!tagFilter.value || paper.tags.includes(tagFilter.value)) && [paper.title, paper.authors, paper.tags.join(' ')].join(' ').toLowerCase().includes(query.value.toLowerCase())))

async function addPaper() {
  if (!newPaper.value.title.trim()) { notice.value = 'Enter a paper title.'; return }
  busy.value = true
  const paper: ManagedPaper = { ...newPaper.value, id: newId(), tags: [], status: 'recommended', recommendedAt: today(), noteIds: [], paperUrl: newPaper.value.paperUrl }
  try {
    const saved = await store.createPaper(paper)
    selected.value = saved
    showAdd.value = false
    notice.value = 'Recommended paper saved.'
    newPaper.value = { title: '', authors: '', venue: '', year: new Date().getFullYear(), topic: '', reason: '', abstract: '', paperUrl: '', doi: '', arxivId: '', publiclyVisible: false }
  } catch (error) {
    const response = (error as Error & { response?: { data?: { detail?: string } } }).response
    notice.value = response?.data?.detail || 'This paper already exists or could not be saved.'
  } finally { busy.value = false }
}

function exportPapers() {
  const url = URL.createObjectURL(new Blob([JSON.stringify(papers.value, null, 2)], { type: 'application/json' }))
  const link = document.createElement('a')
  link.href = url
  link.download = 'recommended-papers.json'
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
</script>

<template>
  <div>
    <DashboardPageHeader :title="$t('Recommended papers')" :description="$t('A memory of what AI has already recommended—and what deserves your attention.')">
      <AppButton variant="secondary" @click="exportPapers"><Download :size="15" /> {{ $t("Export for AI") }}</AppButton>
      <AppButton @click="showAdd = !showAdd"><Plus :size="15" /> {{ $t("Add paper") }}</AppButton>
    </DashboardPageHeader>
    <p v-if="notice" class="feedback" role="status">{{ $t(notice) }}</p>
    <form v-if="showAdd" class="record-editor new-paper-form" @submit.prevent="addPaper">
      <h2>{{ $t("Add recommended paper") }}</h2>
      <div class="field-grid">
        <label>{{ $t("Title") }}<input v-model="newPaper.title" required /></label>
        <label>{{ $t("Authors") }}<input v-model="newPaper.authors" /></label>
        <label>{{ $t("Venue") }}<input v-model="newPaper.venue" /></label>
        <label>{{ $t("Year") }}<input v-model.number="newPaper.year" type="number" required /></label>
        <label>{{ $t("Topic") }}<input v-model="newPaper.topic" /></label>
        <label>{{ $t("Paper URL") }}<input v-model="newPaper.paperUrl" type="url" /></label>
        <label>{{ $t("DOI") }}<input v-model="newPaper.doi" /></label>
        <label>{{ $t("arXiv ID") }}<input v-model="newPaper.arxivId" /></label>
      </div>
      <label>{{ $t("Recommendation reason") }}<textarea v-model="newPaper.reason" rows="2" /></label>
      <label>{{ $t("Abstract") }}<textarea v-model="newPaper.abstract" rows="3" /></label>
      <label class="check-field"><input v-model="newPaper.publiclyVisible" type="checkbox" /> {{ $t("Publish this recommendation on the public paper page") }}</label>
      <div class="editor-actions">
        <AppButton type="submit" :disabled="busy">{{ busy ? $t('Saving…') : $t('Add paper') }}</AppButton>
        <button type="button" @click="showAdd = false">{{ $t("Cancel") }}</button>
      </div>
    </form>
    <section class="paper-toolbar">
      <div class="paper-tabs">
        <button v-for="tab in tabs" :key="tab.value" type="button" :class="{ active: active === tab.value }" @click="active = tab.value">
          {{ $t(tab.label) }}<span>{{ tab.value === 'all' ? papers.length : papers.filter(p => p.status === tab.value).length }}</span>
        </button>
      </div>
      <div class="paper-tools">
        <label class="search-field"><Search :size="15" /><input v-model="query" :placeholder="$t('Search papers, authors, tags…')" /></label>
        <select v-model="tagFilter" :aria-label="$t('Filter by tag')"><option value="">{{ $t("All tags") }}</option><option v-for="tag in allTags" :key="tag">{{ tag }}</option></select>
      </div>
    </section>
    <section class="paper-list">
      <div class="paper-list-head"><span>{{ $t("Status") }}</span><span>{{ $t("Paper") }}</span><span>{{ $t("Topic") }}</span><span>{{ $t("Recommended") }}</span></div>
      <button v-for="paper in filtered" :key="paper.id" class="paper-list-row" type="button" @click="selected = paper">
        <div><AppBadge :tone="paperStatusMeta[paper.status].tone">{{ $t(paperStatusMeta[paper.status].label) }}</AppBadge></div>
        <div class="paper-title-cell">
          <strong>{{ paper.title }}</strong>
          <span>{{ paper.authors }} · {{ paper.venue }} {{ paper.year }}</span>
          <div class="paper-tags"><i v-for="tag in paper.tags" :key="tag">{{ tag }}</i></div>
        </div>
        <span class="paper-topic">{{ paper.topic }}</span>
        <time>{{ paper.recommendedAt }}</time>
      </button>
      <div v-if="!filtered.length" class="empty-state"><BookOpenText :size="26" /><h3>{{ $t("No matching papers") }}</h3><p>{{ $t("Try another search or reading status.") }}</p></div>
    </section>
    <PaperDrawer :paper="selected" @close="selected = null" />
  </div>
</template>
