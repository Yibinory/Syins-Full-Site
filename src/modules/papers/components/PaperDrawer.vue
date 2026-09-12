<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowUpRight, Calendar, Copy, Star, X } from 'lucide-vue-next'
import AppBadge from '@/components/ui/AppBadge.vue'
import TagEditor from '@/components/shared/TagEditor.vue'
import { useWorkspaceStore, type ManagedPaper } from '@/stores/workspace'
import { paperStatusMeta } from '../data'

const props = defineProps<{ paper: ManagedPaper | null }>()
defineEmits<{ close: [] }>()
const store = useWorkspaceStore()
const noteQuery = ref('')
const notice = ref('')
const available = computed(() => store.documents.filter(note => !note.trashedAt && [note.title, note.tags.join(' ')].join(' ').toLowerCase().includes(noteQuery.value.toLowerCase())))
const linked = computed(() => props.paper?.noteIds.map(id => ({ id, note: store.documents.find(note => note.id === id) })) || [])
const paperURL = computed(() => props.paper?.paperUrl || (props.paper?.arxivId ? 'https://arxiv.org/abs/' + props.paper.arxivId : props.paper?.doi ? 'https://doi.org/' + props.paper.doi : ''))
watch(() => props.paper?.id, () => { noteQuery.value = ''; notice.value = '' })
let syncing = false
watch(() => props.paper ? { status: props.paper.status, paperUrl: props.paper.paperUrl, tags: [...props.paper.tags], publiclyVisible: props.paper.publiclyVisible } : null, async (next, previous) => {
  if (!next || !previous || syncing || JSON.stringify(next) === JSON.stringify(previous) || !props.paper) return
  syncing = true
  try { await store.updatePaper(props.paper); notice.value = 'Paper changes saved.' }
  catch (error) {
    const response = (error as Error & { response?: { data?: { detail?: string } } }).response
    notice.value = response?.data?.detail || 'Paper changes could not be saved.'
  } finally { syncing = false }
})
async function toggle(id: number) { if (!props.paper) return; await store.linkNote(props.paper.id, id, !props.paper.noteIds.includes(id)) }
async function copy() {
  if (!props.paper) return
  try { await navigator.clipboard.writeText(props.paper.authors + '. ' + props.paper.title + '. ' + props.paper.venue + ', ' + props.paper.year + '.'); notice.value = 'Citation copied.' }
  catch { notice.value = 'Clipboard unavailable. Select and copy the paper details above.' }
}
</script>

<template>
  <Transition name="drawer">
    <div v-if="paper" class="drawer-layer" @keydown.esc="$emit('close')">
      <button class="drawer-backdrop" :aria-label="$t('Close paper details')" @click="$emit('close')" />
      <aside class="paper-drawer" role="dialog" aria-modal="true" :aria-label="$t('Paper details')">
        <header>
          <div>
            <p>{{ $t("Paper #") }}{{ paper.id }}</p>
            <AppBadge :tone="paperStatusMeta[paper.status].tone">{{ $t(paperStatusMeta[paper.status].label) }}</AppBadge>
          </div>
          <button :aria-label="$t('Close')" @click="$emit('close')"><X :size="19" /></button>
        </header>

        <div class="paper-drawer-body">
          <p class="drawer-venue">{{ paper.venue }} · {{ paper.year }}</p>
          <h2>{{ paper.title }}</h2>
          <p class="drawer-authors">{{ paper.authors }}</p>
          <div v-if="paper.rating" class="paper-rating"><Star v-for="n in 5" :key="n" :size="15" :fill="n <= paper.rating ? 'currentColor' : 'none'" /></div>

          <section><h3>{{ $t("Why it was recommended") }}</h3><p>{{ paper.reason }}</p></section>
          <section><h3>{{ $t("Abstract") }}</h3><p>{{ paper.abstract }}</p></section>
          <section>
            <h3>{{ $t("Research context") }}</h3>
            <div class="detail-grid">
              <span>{{ $t("Topic") }}<strong>{{ paper.topic }}</strong></span>
              <span>{{ $t("Recommended") }}<strong><Calendar :size="13" /> {{ paper.recommendedAt }}</strong></span>
              <span v-if="paper.doi">{{ $t("DOI") }}<strong>{{ paper.doi }}</strong></span>
              <span v-if="paper.arxivId">{{ $t("arXiv") }}<strong>{{ paper.arxivId }}</strong></span>
            </div>
          </section>

          <section class="drawer-edit-fields">
            <label>{{ $t("Reading status") }} <select v-model="paper.status"><option v-for="(meta, key) in paperStatusMeta" :key="key" :value="key">{{ $t(meta.label) }}</option></select>
            </label>
            <label>{{ $t("Paper URL") }}<input v-model="paper.paperUrl" :placeholder="$t('https://…')" /></label>
            <label class="check-field"><input v-model="paper.publiclyVisible" type="checkbox" /> {{ $t("Show on public recommendation page") }}</label>
            <TagEditor v-model="paper.tags" />
          </section>

          <section class="linked-notes">
            <div class="editor-heading">
              <h3>{{ $t("Linked notes") }} <small>{{ paper.noteIds.length }}</small></h3>
              <RouterLink :to="{ path: '/dashboard/docs', query: { new: '1', paper: paper.id } }">{{ $t("New linked note ↗") }}</RouterLink>
            </div>
            <p v-if="!linked.length">{{ $t("No notes linked. Reading a paper does not require a note.") }}</p>
            <ul>
              <li v-for="item in linked" :key="item.id">
                <RouterLink v-if="item.note && !item.note.trashedAt" :to="{ path: '/dashboard/docs', query: { note: item.id } }">{{ item.note.title }}</RouterLink>
                <span v-else>{{ item.note?.title || $t('Missing note') }} · {{ item.note?.trashedAt ? $t('In Trash') : $t('Unavailable') }}</span>
                <button type="button" class="text-action" @click="toggle(item.id)">{{ $t("Unlink") }}</button>
              </li>
            </ul>
            <input v-model="noteQuery" :aria-label="$t('Search notes to link')" :placeholder="$t('Find an existing note…')" />
            <div class="note-link-options">
              <label v-for="note in available" :key="note.id">
                <input type="checkbox" :checked="paper.noteIds.includes(note.id)" @change="toggle(note.id)" />
                <span>{{ note.title }}<small>{{ note.visibility }} · {{ $t(note.kind) }}</small></span>
              </label>
              <p v-if="!available.length">{{ $t("No matching notes.") }}</p>
            </div>
            <p class="muted-copy">{{ $t("You can link any number of notes. Unlinking keeps the document.") }}</p>
          </section>
          <p class="feedback" role="status">{{ notice || $t('Changes are saved to the workspace database.') }}</p>
        </div>

        <footer>
          <button @click="copy"><Copy :size="15" /> {{ $t("Copy citation") }}</button>
          <a v-if="paperURL" :href="paperURL" target="_blank" rel="noopener noreferrer">{{ $t("Open paper") }} <ArrowUpRight :size="15" /></a>
        </footer>
      </aside>
    </div>
  </Transition>
</template>
