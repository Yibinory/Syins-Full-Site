<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowUpRight, Copy } from 'lucide-vue-next'
import PublicLayout from '@/layouts/PublicLayout.vue'
import type { PublicationType } from '../data'
import ResearchMedia from '@/components/shared/ResearchMedia.vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { storeToRefs } from 'pinia'
const { publications } = storeToRefs(useWorkspaceStore())
const copyNotice = ref('')
async function copyBibtex(text: string) { try { await navigator.clipboard.writeText(text); copyNotice.value = 'BibTeX copied.' } catch { copyNotice.value = 'Clipboard unavailable.' } }
import { useSiteContentStore } from '@/stores/siteContent'

const siteContent = useSiteContentStore()

const filters: Array<'All' | PublicationType> = ['All', 'Conference', 'Journal', 'Preprint']
const active = ref<(typeof filters)[number]>('All')
const grouped = computed(() => {
  const items = active.value === 'All' ? publications.value : publications.value.filter((p) => p.type === active.value)
  return items.reduce<Record<number, typeof publications.value>>((groups, paper) => {
    ;(groups[paper.year] ??= []).push(paper)
    return groups
  }, {})
})
</script>

<template>
  <PublicLayout>
    <header class="public-page-intro publications-intro page-grid">
      <p class="section-kicker">{{ $t("Publications") }}</p><h1>{{ siteContent.localized.publicationsHeading }}</h1><p>{{ siteContent.localized.publicationsDescription }}</p>
    </header>
    <section class="publication-browser page-grid">
      <div class="publication-filters" :aria-label="$t('Filter publications')"><button v-for="filter in filters" :key="filter" :class="{ active: active === filter }" @click="active = filter">{{ $t(filter) }}</button></div>
      <div class="publication-years"><p v-if="copyNotice" role="status">{{ $t(copyNotice) }}</p><p v-if="!Object.keys(grouped).length">{{ $t("No publications in this category.") }}</p>
        <section v-for="(papers, year) in grouped" :key="year" class="publication-year-group"><h2>{{ year }}</h2><article v-for="paper in papers" :key="paper.id" class="publication-entry"><ResearchMedia v-if="paper.mediaAssetId || paper.mediaUrl" :project="paper" /><div v-else class="publication-thumb"><span>{{ paper.venueShort }}</span></div><div class="publication-entry-copy"><p class="pub-venue">{{ paper.venueShort }} · {{ paper.type }}</p><h3>{{ paper.title }}</h3><p class="pub-authors">{{ paper.authors }}</p><p v-if="paper.motivation" class="publication-motivation">{{ paper.motivation }}</p><p v-if="paper.approach">{{ paper.approach }}</p><details v-if="paper.abstract"><summary>{{ $t("Abstract") }}</summary><p>{{ paper.abstract }}</p></details><div class="tag-list"><span v-for="tag in paper.tags" :key="tag">{{ tag }}</span></div><div class="publication-actions"><a v-if="paper.paperUrl" :href="paper.paperUrl">{{ $t("Paper") }} <ArrowUpRight :size="14" /></a><a v-if="paper.codeUrl" :href="paper.codeUrl">{{ $t("Code") }} <ArrowUpRight :size="14" /></a><a v-if="paper.projectUrl" :href="paper.projectUrl">{{ $t("Project") }} <ArrowUpRight :size="14" /></a><button v-if="paper.bibtex" @click="copyBibtex(paper.bibtex)"><Copy :size="13" /> {{ $t("BibTeX") }}</button></div></div></article></section>
      </div>
    </section>
  </PublicLayout>
</template>
