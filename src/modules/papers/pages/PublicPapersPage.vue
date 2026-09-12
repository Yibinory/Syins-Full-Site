<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { ArrowUpRight, LockKeyhole, Search } from 'lucide-vue-next'
import PublicLayout from '@/layouts/PublicLayout.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import { listData } from '@/services/api'
import { papersApi, type PublicPaper } from '../api'

const papers = ref<PublicPaper[]>([])
const selectedId = ref<number | null>(null)
const query = ref('')
const loading = ref(true)
const error = ref('')
const detail = ref<HTMLElement | null>(null)

const filtered = computed(() => {
  const needle = query.value.trim().toLowerCase()
  if (!needle) return papers.value
  return papers.value.filter(paper => [paper.title, paper.authors, paper.topic, paper.tags.join(' ')].join(' ').toLowerCase().includes(needle))
})
const selected = computed(() => filtered.value.find(paper => paper.id === selectedId.value) ?? filtered.value[0] ?? null)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const response = await papersApi.publicList()
    papers.value = listData<PublicPaper>(response.data)
    if (papers.value.length && selectedId.value === null) selectedId.value = papers.value[0].id
  } catch {
    error.value = 'Recommended papers are temporarily unavailable.'
  } finally {
    loading.value = false
  }
}

async function selectPaper(id: number) {
  selectedId.value = id
  await nextTick()
  if (window.matchMedia('(max-width: 900px)').matches) {
    detail.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    detail.value?.focus({ preventScroll: true })
  }
}

onMounted(load)
</script>

<template>
  <PublicLayout>
    <section class="public-paper-intro page-grid">
      <p class="section-kicker">{{ $t("04 / RECOMMENDED PAPERS") }}</p>
      <h1>{{ $t("Papers worth") }}<br /><em>{{ $t("returning to.") }}</em></h1>
      <p>{{ $t("A reading collection on medical imaging, generalization and generation. Recommendations, context and linked notes, newest first.") }}</p>
    </section>

    <section class="public-paper-browser page-grid">
      <div class="public-paper-toolbar">
        <label class="public-paper-search"><Search :size="15" /><input v-model="query" :aria-label="$t('Search recommended papers')" :placeholder="$t('Search papers, authors, topics…')" /></label>
        <span>{{ filtered.length }} {{ $t("papers") }}</span>
      </div>
      <p v-if="loading" class="public-paper-state">{{ $t("Loading the paper memory…") }}</p>
      <div v-else-if="error" class="public-paper-state"><p>{{ $t(error) }}</p><button type="button" @click="load">{{ $t("Try again") }}</button></div>
      <p v-else-if="!filtered.length" class="public-paper-state">{{ $t("No public recommendations match this search.") }}</p>
      <div v-else class="public-paper-layout">
        <div class="public-paper-list">
          <button v-for="paper in filtered" :key="paper.id" class="public-paper-row" :class="{ selected: paper.id === selected?.id }" :aria-pressed="paper.id === selected?.id" type="button" @click="selectPaper(paper.id)">
            <span class="public-paper-row-date">{{ paper.recommendedAt }}</span>
            <strong>{{ paper.title }}</strong>
            <span>{{ paper.authors }} · {{ paper.venue }} {{ paper.year }}</span>
            <div class="paper-tags"><i v-for="tag in paper.tags" :key="tag">{{ tag }}</i></div>
          </button>
        </div>

        <article v-if="selected" ref="detail" class="public-paper-detail" tabindex="-1" :aria-label="$t('Selected paper')">
          <header>
            <p class="section-kicker">{{ selected.topic || $t('Research literature') }} · {{ selected.recommendedAt }}</p>
            <AppBadge tone="info">{{ $t(selected.status.replace('_', ' ')) }}</AppBadge>
            <h2>{{ selected.title }}</h2>
            <p class="public-paper-authors">{{ selected.authors }}</p>
            <p class="public-paper-venue">{{ selected.venue }}<span v-if="selected.year"> · {{ selected.year }}</span></p>
            <div class="public-paper-actions">
              <a v-if="selected.paperUrl" :href="selected.paperUrl" target="_blank" rel="noopener noreferrer">{{ $t("Open paper") }} <ArrowUpRight :size="14" /></a>
              <span v-if="selected.doi">{{ $t("DOI") }} {{ selected.doi }}</span>
              <span v-if="selected.arxivId">{{ $t("arXiv") }} {{ selected.arxivId }}</span>
            </div>
          </header>
          <section v-if="selected.reason || selected.abstract" class="public-paper-context">
            <div v-if="selected.reason"><small>{{ $t("Why it was recommended") }}</small><p>{{ selected.reason }}</p></div>
            <div v-if="selected.abstract"><small>{{ $t("Abstract") }}</small><p>{{ selected.abstract }}</p></div>
          </section>
          <section class="public-paper-notes">
            <div class="public-paper-section-heading"><span>{{ $t("Linked notes") }}</span><b>{{ selected.notes.length }}</b></div>
            <p v-if="!selected.notes.length" class="muted-copy">{{ $t("No notes have been linked to this paper yet.") }}</p>
            <article v-for="note in selected.notes" :key="note.id" class="public-linked-note">
              <header><div><span class="section-kicker">{{ $t(note.kind) }} · {{ note.publishedAt || $t('Undated') }}</span><h3><RouterLink :to="note.requiresAuth ? { path: '/login', query: { redirect: '/notes/' + note.slug } } : '/notes/' + note.slug">{{ note.title }}</RouterLink></h3></div><LockKeyhole v-if="note.requiresAuth" :size="16" /></header>
              <p v-if="note.summary">{{ note.summary }}</p>
              <div class="note-entry-tags"><i v-for="tag in note.tags" :key="tag">{{ tag }}</i></div>
              <p class="public-note-meta">{{ note.readingTime }}</p>
              <template v-if="note.requiresAuth">
                <RouterLink class="paper-note-login" :to="{ path: '/login', query: { redirect: '/notes/' + note.slug } }">{{ $t("Sign in to read this private note →") }}</RouterLink>
              </template>
              <template v-else>
                <RouterLink :to="'/notes/' + note.slug">{{ $t("Open note page ↗") }}</RouterLink>
              </template>
            </article>
          </section>
        </article>
      </div>
    </section>
  </PublicLayout>
</template>
