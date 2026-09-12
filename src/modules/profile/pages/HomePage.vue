<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ArrowDownRight, ArrowUpRight, Plus } from 'lucide-vue-next'
import PublicLayout from '@/layouts/PublicLayout.vue'
import { useWorkspaceStore } from '@/stores/workspace'
import ResearchMedia from '@/components/shared/ResearchMedia.vue'
import { useSiteContentStore } from '@/stores/siteContent'

const siteContent = useSiteContentStore()

const fallbackCurrentResearch = [
  { number: '01', title: 'Medical Image Generation', text: 'Controllable generative models that preserve anatomy while exposing clinically meaningful variation.', status: 'Active', question: 'How can pathology change without silently changing patient identity?', method: 'Anatomy-conditioned diffusion · Counterfactual editing', updated: 'Updated 2 days ago' },
  { number: '02', title: 'Longitudinal Image Modeling', text: 'Learning patient-specific trajectories to model disease progression across sparse clinical timepoints.', status: 'Exploring', question: 'What does a plausible future image look like when observations are sparse and irregular?', method: 'Temporal latent models · Calibrated uncertainty', updated: 'Updated today' },
  { number: '03', title: 'Domain Generalization', text: 'Robust representations that transfer across scanners, institutions, and unseen acquisition protocols.', status: 'Active', question: 'Which visual features survive a change of hospital, scanner, and population?', method: 'Invariant representation learning · OOD evaluation', updated: 'Updated 5 days ago' },
]
const currentResearch = computed(() => siteContent.content.currentResearch?.length ? siteContent.content.currentResearch : fallbackCurrentResearch)

const workspace = useWorkspaceStore()
const publications = computed(() => workspace.publications.filter(p => p.featured).sort((a, b) => b.year - a.year))
const featuredNote = computed(() => workspace.documents.filter(n => n.visibility === 'public' && !n.trashedAt).sort((a, b) => Number(b.featured) - Number(a.featured) || (b.publishedAt || '').localeCompare(a.publishedAt || ''))[0])

const portrait = ref<HTMLElement | null>(null)
const lens = reactive({ x: 160, y: 190, visible: false, pinned: false })
const lensStyle = computed(() => ({ left: `${lens.x}px`, top: `${lens.y}px`, backgroundPosition: `${Math.max(0, Math.min(100, lens.x / (portrait.value?.clientWidth || 1) * 100))}% ${Math.max(0, Math.min(100, lens.y / (portrait.value?.clientHeight || 1) * 100))}%` }))
const activeResearch = ref(0)
function moveLens(event: PointerEvent) {
  const rect = portrait.value?.getBoundingClientRect()
  if (!rect) return
  lens.x = Math.max(55, Math.min(rect.width - 55, event.clientX - rect.left))
  lens.y = Math.max(55, Math.min(rect.height - 55, event.clientY - rect.top))
}

function toggleLens() {
  lens.pinned = !lens.pinned
  lens.visible = lens.pinned
}
</script>

<template>
  <PublicLayout>
    <section class="hero page-grid">
      <div class="hero-copy">
        <p class="eyebrow"><span>{{ $t("01 — Identity") }}</span><span>{{ siteContent.content.title }} · {{ siteContent.content.location }}</span></p>
        <h1><span v-for="(part, index) in siteContent.content.name.split(' ')" :key="index">{{ part }}</span></h1>
        <p class="hero-headline">{{ siteContent.content.headline }}</p>
        <p class="hero-bio">{{ siteContent.content.bio }}</p>
        <div class="hero-links">
          <a v-for="link in [{ label: 'Google Scholar', href: siteContent.content.scholarUrl }, { label: 'GitHub', href: siteContent.content.githubUrl }, { label: 'Curriculum Vitae', href: siteContent.content.cvUrl }]" :key="link.label" :href="link.href">{{ link.label }} <ArrowUpRight :size="15" /></a>
          <a :href="`mailto:${siteContent.content.email}`">{{ $t("Email") }} <ArrowUpRight :size="15" /></a>
        </div>
      </div>
      <figure ref="portrait" class="portrait-wrap portrait-interactive" @pointermove="moveLens" @pointerenter="lens.visible = true" @pointerleave="lens.visible = lens.pinned" @click="toggleLens">
        <img class="portrait-image" src="/images/syins-yibinory-portrait-mock.png" :alt="$t('Portrait of Syins Yibinory in a medical imaging research studio')" />
        <div class="portrait-lens" :class="{ visible: lens.visible }" :style="lensStyle" aria-hidden="true"><span>{{ $t("RESEARCH LENS") }}</span></div>
        <span class="lens-instruction">{{ $t("Move to reveal the research") }}</span>
        <span class="portrait-axis">{{ $t("SUBJECT — RESEARCHER") }}</span>
        <i class="portrait-corner portrait-corner--a" /><i class="portrait-corner portrait-corner--b" />
        <figcaption><span>{{ $t("FIG. HD—01 / 2026") }}</span><span>{{ $t("Researching images in motion") }}</span></figcaption>
      </figure>
      <a href="#selected-research" class="scroll-note">{{ $t("Selected work below") }} <ArrowDownRight :size="17" /></a>
    </section>

    <div class="research-vocabulary" :aria-label="$t('Research directions')">
      <template v-for="(direction, index) in siteContent.content.researchDirections.split('×')" :key="index">
        <i v-if="index" aria-hidden="true">×</i><span>{{ direction.trim() }}</span>
      </template>
    </div>

    <section id="research" class="current page-grid">
      <div class="section-heading">
        <p class="section-kicker">{{ $t("02 — Current research") }}</p>
        <h2>{{ siteContent.content.currentResearchHeading }}</h2>
      </div>
      <div class="research-list">
        <button v-for="(item, index) in currentResearch" :key="item.number" class="research-row" :class="{ active: activeResearch === index }" :aria-pressed="activeResearch === index" @mouseenter="activeResearch = index" @focus="activeResearch = index" @click="activeResearch = index">
          <span class="row-number">{{ item.number }}</span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.text }}</p>
          <span class="research-status"><i />{{ item.status }} <Plus :size="13" /></span>
        </button>
        <div class="research-detail" aria-live="polite">
          <span class="detail-number">{{ currentResearch[activeResearch].number }}</span>
          <div><p>{{ $t("Research question") }}</p><h3>{{ currentResearch[activeResearch].question }}</h3></div>
          <div><p>{{ $t("Current approach") }}</p><strong>{{ currentResearch[activeResearch].method }}</strong><small>{{ currentResearch[activeResearch].updated }}</small></div>
        </div>
      </div>
    </section>

    <section id="selected-research" class="selected-work page-grid">
      <div class="section-heading work-heading">
        <p class="section-kicker">{{ $t("03 — Selected research") }}</p>
        <h2>{{ siteContent.content.featuredResearchHeading }}</h2>
        <p class="work-aside">{{ siteContent.content.featuredResearchIntro }}</p>
      </div>
      <article v-for="(project, index) in siteContent.content.selectedProjects" :key="project.id" class="feature-project" :class="{ 'feature-project--reverse': index % 2 === 1 }">
        <ResearchMedia :project="project" />
        <div class="project-copy">
          <span class="project-index">{{ $t("Project") }} {{ String(index + 1).padStart(2, '0') }} · {{ project.status }}</span>
          <h3>{{ project.title }}</h3>
          <p class="research-question">{{ project.motivation }}</p>
          <p>{{ project.approach }}</p>
          <div class="project-links">
            <template v-for="(link, linkIndex) in project.links" :key="linkIndex">
              <a v-if="link.url" :href="link.url">{{ link.label }} <ArrowUpRight :size="15" /></a>
              <span v-else class="project-link-pending">{{ link.label }} {{ $t("· Coming soon") }}</span>
            </template>
          </div>
        </div>
      </article>
    </section>

    <section class="publications-preview page-grid">
      <div class="section-heading publications-title">
        <p class="section-kicker">{{ $t("Selected publications") }}</p>
        <h2>{{ $t("Selected publications") }}</h2>
        <RouterLink to="/publications">{{ $t("View all publications") }} <ArrowUpRight :size="15" /></RouterLink>
      </div>
      <div class="publication-list">
        <article v-for="paper in publications" :key="paper.title" class="publication-row">
          <div class="pub-year">{{ paper.year }}</div>
          <div><p class="pub-venue">{{ paper.venueShort }}</p><h3>{{ paper.title }}</h3><p class="pub-authors">{{ paper.authors }}</p><div class="tag-list"><span v-for="tag in paper.tags" :key="tag">{{ tag }}</span></div></div>
          <a v-if="paper.paperUrl" :href="paper.paperUrl" :aria-label="$t('Open publication')"><ArrowUpRight :size="20" /></a>
        </article>
      </div>
    </section>

    <section v-if="featuredNote" class="notes-preview page-grid">
      <div><p class="section-kicker">{{ $t("Notes & writing") }}</p><h2>{{ $t("Thinking in public.") }}</h2></div>
      <article><time>{{ featuredNote.publishedAt || featuredNote.displayDate }}</time><h3>{{ featuredNote.title }}</h3><p>{{ featuredNote.summary }}</p><RouterLink :to="`/notes/${featuredNote.slug}`">{{ $t("Read note") }} <ArrowUpRight :size="15" /></RouterLink></article>
    </section>
  </PublicLayout>
</template>
