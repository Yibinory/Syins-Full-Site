<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowDownRight, ArrowUpRight, BookOpen, FileText } from 'lucide-vue-next'
import PublicLayout from '@/layouts/PublicLayout.vue'
import { useWorkspaceStore } from '@/stores/workspace'
const workspace = useWorkspaceStore()
const publicNotes = computed(() => workspace.documents.filter(n => n.visibility === 'public' && !n.trashedAt))
import type { NoteKind, PublicNote } from '../types'
import { useSiteContentStore } from '@/stores/siteContent'

const siteContent = useSiteContentStore()

type NoteFilter = 'All' | NoteKind

const filters: NoteFilter[] = ['All', 'Research Note', 'Essay', 'Guide', 'Reference']
const activeFilter = ref<NoteFilter>('All')
const selectedId = ref<number | null>(null)
const selectedNote = computed(() => publicNotes.value.find(n => n.id === selectedId.value) ?? publicNotes.value.find(n => n.featured) ?? publicNotes.value[0])
const visibleNotes = computed(() => activeFilter.value === 'All'
  ? publicNotes.value
  : publicNotes.value.filter((note) => note.kind === activeFilter.value))

function chooseNote(note: PublicNote) {
  selectedId.value = note.id
  document.querySelector('#selected-note')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
</script>

<template>
  <PublicLayout>
    <header class="notes-intro page-grid">
      <p class="section-kicker">Notes / 2026</p>
      <h1>{{ siteContent.content.notesHeading }}</h1>
      <div class="notes-intro-copy">
        <p>{{ siteContent.content.notesDescription }}</p>
        <a href="#note-index">Explore the index <ArrowDownRight :size="16" /></a>
      </div>
      <p class="notes-count"><strong>{{ publicNotes.length }}</strong><span>published entries</span></p>
    </header>

    <section v-if="selectedNote" id="selected-note" class="featured-note page-grid" aria-live="polite">
      <div class="featured-note-meta">
        <span>Selected note</span>
        <span>{{ selectedNote.kind }}</span>
        <time :datetime="selectedNote.publishedAt">{{ selectedNote.displayDate }}</time>
      </div>
      <div class="featured-note-copy">
        <p class="featured-note-index">N—{{ String(selectedNote.id).padStart(2, '0') }}</p>
        <h2>{{ selectedNote.title }}</h2>
        <p>{{ selectedNote.excerpt }}</p>
        <RouterLink :to="`/notes/${selectedNote.slug}`">Read note <ArrowUpRight :size="16" /></RouterLink>
      </div>
      <figure class="featured-note-figure">
        <img src="/images/longitudinal-mri-mock.png" alt="Longitudinal MRI study figure" />
        <figcaption><span>RESEARCH ARCHIVE</span><span>{{ selectedNote.readingTime }}</span></figcaption>
      </figure>
    </section>

    <section id="note-index" class="notes-library page-grid">
      <div class="notes-library-heading">
        <p class="section-kicker">Index</p>
        <h2>Browse the library.</h2>
        <p>One Markdown collection, structured by format and topic. Some entries are finished essays; others remain living research documents.</p>
      </div>

      <div class="notes-index">
        <div class="note-filters" aria-label="Filter notes by format">
          <button v-for="filter in filters" :key="filter" type="button" :class="{ active: activeFilter === filter }" :aria-pressed="activeFilter === filter" @click="activeFilter = filter">
            {{ filter }}
            <span>{{ filter === 'All' ? publicNotes.length : publicNotes.filter((note) => note.kind === filter).length }}</span>
          </button>
        </div>

        <div class="note-list"><p v-if="!visibleNotes.length">No public notes in this category.</p>
          <button v-for="note in visibleNotes" :key="note.id" type="button" class="note-entry" :class="{ selected: selectedNote?.id === note.id }" @click="chooseNote(note)">
            <span class="note-entry-icon"><BookOpen v-if="note.kind === 'Research Note' || note.kind === 'Reference'" :size="16" /><FileText v-else :size="16" /></span>
            <span class="note-entry-main">
              <small>{{ note.kind }}</small>
              <strong>{{ note.title }}</strong>
              <span>{{ note.summary }}</span>
            </span>
            <span class="note-entry-tags"><i v-for="tag in note.tags" :key="tag">{{ tag }}</i></span>
            <span class="note-entry-date"><time :datetime="note.publishedAt">{{ note.displayDate }}</time><small>{{ note.readingTime }}</small></span>
            <ArrowUpRight class="note-entry-arrow" :size="18" />
          </button>
        </div>
      </div>
    </section>
  </PublicLayout>
</template>
