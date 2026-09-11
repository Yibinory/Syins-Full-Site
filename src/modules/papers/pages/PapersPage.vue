<script setup lang="ts">
import { computed, ref } from 'vue'
import { BookOpenText, Download, Filter, Plus, Search, SlidersHorizontal } from 'lucide-vue-next'
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
const newPaper = ref({ title: '', authors: '', venue: '', year: new Date().getFullYear(), topic: '', reason: '', abstract: '', paperUrl: '' })
async function addPaper() { if (!newPaper.value.title.trim()) return; const paper: ManagedPaper = { ...newPaper.value, id: newId(), tags: [], status: 'recommended', recommendedAt: today(), noteIds: [] }; const saved = await store.createPaper(paper); selected.value = saved; showAdd.value = false; newPaper.value = { title: '', authors: '', venue: '', year: new Date().getFullYear(), topic: '', reason: '', abstract: '', paperUrl: '' } }
function exportPapers() { const url = URL.createObjectURL(new Blob([JSON.stringify(papers.value, null, 2)], { type: 'application/json' })); const a = document.createElement('a'); a.href = url; a.download = 'recommended-papers.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000) }
const selected = ref<ManagedPaper | null>(null)
const filtered = computed(() => papers.value.filter((paper) => (active.value === 'all' || paper.status === active.value) && (!tagFilter.value || paper.tags.includes(tagFilter.value)) && `${paper.title} ${paper.authors} ${paper.tags.join(' ')}`.toLowerCase().includes(query.value.toLowerCase())))
</script>
<template><div><DashboardPageHeader title="Recommended papers" description="A memory of what AI has already recommended—and what deserves your attention."><AppButton variant="secondary" @click="exportPapers"><Download :size="15" /> Export for AI</AppButton><AppButton @click="showAdd = !showAdd"><Plus :size="15" /> Add paper</AppButton></DashboardPageHeader><form v-if="showAdd" class="record-editor new-paper-form" @submit.prevent="addPaper"><h2>Add recommended paper</h2><div class="field-grid"><label>Title<input v-model="newPaper.title" required /></label><label>Authors<input v-model="newPaper.authors" /></label><label>Venue<input v-model="newPaper.venue" /></label><label>Year<input v-model.number="newPaper.year" type="number" required /></label><label>Topic<input v-model="newPaper.topic" /></label><label>Paper URL<input v-model="newPaper.paperUrl" type="url" /></label></div><label>Recommendation reason<textarea v-model="newPaper.reason" rows="2" /></label><label>Abstract<textarea v-model="newPaper.abstract" rows="3" /></label><div class="editor-actions"><AppButton type="submit">Add paper</AppButton><button type="button" @click="showAdd = false">Cancel</button></div></form><section class="paper-toolbar"><div class="paper-tabs"><button v-for="tab in tabs" :key="tab.value" :class="{ active: active === tab.value }" @click="active = tab.value">{{ tab.label }}<span>{{ tab.value === 'all' ? papers.length : papers.filter((p) => p.status === tab.value).length }}</span></button></div><div class="paper-tools"><label class="search-field"><Search :size="15" /><input v-model="query" placeholder="Search papers, authors, tags…" /></label><select v-model="tagFilter" aria-label="Filter by tag"><option value="">All tags</option><option v-for="tag in allTags" :key="tag">{{ tag }}</option></select></div></section><section class="paper-list"><div class="paper-list-head"><span>Status</span><span>Paper</span><span>Topic</span><span>Recommended</span></div><button v-for="paper in filtered" :key="paper.id" class="paper-list-row" @click="selected = paper"><div><AppBadge :tone="paperStatusMeta[paper.status].tone">{{ paperStatusMeta[paper.status].label }}</AppBadge></div><div class="paper-title-cell"><strong>{{ paper.title }}</strong><span>{{ paper.authors }} · {{ paper.venue }} {{ paper.year }}</span><div class="paper-tags"><i v-for="tag in paper.tags" :key="tag">{{ tag }}</i></div></div><span class="paper-topic">{{ paper.topic }}</span><time>{{ paper.recommendedAt }}</time></button><div v-if="!filtered.length" class="empty-state"><BookOpenText :size="26" /><h3>No matching papers</h3><p>Try another search or reading status.</p></div></section><PaperDrawer :paper="selected" @close="selected = null" /></div></template>
