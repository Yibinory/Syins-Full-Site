<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import DashboardPageHeader from '@/components/shared/DashboardPageHeader.vue'
import AppButton from '@/components/ui/AppButton.vue'
import TagEditor from '@/components/shared/TagEditor.vue'
import MarkdownBody from '../components/MarkdownBody.vue'
import { newId, today, useWorkspaceStore, type Document } from '@/stores/workspace'
const store = useWorkspaceStore()
const route = useRoute()
const query = ref('')
const filter = ref('all')
const draft = ref<Document | null>(null)
const notice = ref('')
const pendingId = ref<number | null>(null)
const documents = computed(() => store.documents.filter(d => (filter.value === 'trash' ? !!d.trashedAt : !d.trashedAt && (filter.value === 'all' || d.visibility === filter.value)) && `${d.title} ${d.tags.join(' ')}`.toLowerCase().includes(query.value.toLowerCase())))

function edit(doc: Document) {
  draft.value = JSON.parse(JSON.stringify(doc))
  notice.value = ''
  pendingId.value = null
}

function create() {
  const date = today()
  draft.value = {
    id: newId(), slug: `note-${newId()}`, title: '', summary: '', excerpt: '',
    kind: store.settings.defaultNoteKind, publishedAt: date, displayDate: date,
    readingTime: '1 min', tags: [], featured: false, content: '',
    visibility: store.settings.defaultNoteVisibility, updatedAt: date, trashedAt: null,
  }
  notice.value = ''
}
async function save() {
  if (!draft.value?.title.trim()) { notice.value = 'Please enter a title.'; return }
  const doc = JSON.parse(JSON.stringify(draft.value)) as Document
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(doc.slug)) { notice.value = 'Slug must contain lowercase letters, numbers and hyphens.'; return }
  if (store.documents.some(n => n.id !== doc.id && n.slug === doc.slug)) { notice.value = 'This slug is already used by another note.'; return }
  const saved = await store.saveDocument(doc)
  draft.value = JSON.parse(JSON.stringify(saved))
  const paper = store.papers.find(p => p.id === Number(route.query.paper))
  if (paper) await store.linkNote(paper.id, saved.id, true)
  notice.value = paper ? 'Saved and linked to the recommended paper.' : 'Saved to the workspace database.'
}
async function uploadMarkdown(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  try {
    const saved = await store.uploadMarkdown(file, { visibility: store.settings.defaultNoteVisibility, kind: store.settings.defaultNoteKind })
    edit(saved)
    const paper = store.papers.find(p => p.id === Number(route.query.paper))
    if (paper) await store.linkNote(paper.id, saved.id, true)
    notice.value = paper ? 'Markdown uploaded and linked to the recommended paper.' : 'Markdown uploaded to the workspace database.'
  } catch (error) {
    const response = (error as Error & { response?: { data?: { detail?: string } } }).response
    notice.value = response?.data?.detail || 'Markdown upload failed. Use a UTF-8 .md or .markdown file.'
  }
}
async function replaceContent(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || !draft.value) return
  const currentDraft = draft.value
  try {
    if (!/\.(md|markdown)$/i.test(file.name) || file.size > 10 * 1024 * 1024) throw new Error()
    const content = new TextDecoder('utf-8', { fatal: true }).decode(await file.arrayBuffer())
    if (draft.value !== currentDraft) return
    currentDraft.content = content
    notice.value = 'Content replaced. Title, summary, tags and other fields are unchanged. Save the note to apply.'
  } catch { notice.value = 'Use a UTF-8 Markdown file smaller than 10 MB.' }
}
async function trash() {
  const doc = store.documents.find(d => d.id === pendingId.value)
  if (doc) await store.trashDocument(doc.id)
  pendingId.value = null
  draft.value = null
  notice.value = 'Moved to Trash. Existing paper links are retained for restoration.'
}

function openFromRoute() {
  const doc = store.documents.find(d => d.id === Number(route.query.note))
  if (doc) edit(doc)
  else if (route.query.new) create()
}

async function restore() {
  if (!draft.value) return
  await store.restoreDocument(draft.value)
  draft.value.trashedAt = null
  notice.value = 'Restored.'
}
watch(() => route.fullPath, openFromRoute, { immediate: true })
</script>
<template>
  <div>
    <DashboardPageHeader :title="$t('Documents')" :description="$t('Write notes, organize your knowledge, and choose what appears publicly.')">
      <AppButton @click="create">{{ $t("New note") }}</AppButton>
      <label class="upload-markdown-button">
        <span>{{ $t("Upload Markdown") }}</span>
        <input type="file" accept=".md,.markdown,text/markdown" @change="uploadMarkdown" />
      </label>
    </DashboardPageHeader>

    <p v-if="notice" class="feedback" role="status">{{ $t(notice) }}</p>

    <div class="manager-split">
      <section class="record-list">
        <input v-model="query" :aria-label="$t('Search documents')" :placeholder="$t('Search titles or tags…')" />
        <select v-model="filter" :aria-label="$t('Document visibility filter')">
          <option value="all">{{ $t("All active notes") }}</option>
          <option value="private">{{ $t("Private") }}</option>
          <option value="public">{{ $t("Public") }}</option>
          <option value="unlisted">{{ $t("Unlisted") }}</option>
          <option value="trash">{{ $t("Trash") }}</option>
        </select>
        <button v-for="doc in documents" :key="doc.id" class="record-row" :class="{ active: draft?.id === doc.id }" @click="edit(doc)">
          <strong>{{ doc.title }}</strong>
          <small>{{ $t(doc.kind) }} · {{ doc.trashedAt ? $t('Trash') : doc.visibility }} · {{ doc.updatedAt }}</small>
          <span>{{ doc.tags.join(' · ') }}</span>
        </button>
        <p v-if="!documents.length" class="empty-hint">{{ $t("No documents in this view.") }}</p>
      </section>

      <section v-if="draft" class="record-editor">
        <template v-if="draft.trashedAt">
          <h2>{{ draft.title }}</h2>
          <p>{{ $t("This note is in Trash and is not visible publicly.") }}</p>
          <AppButton @click="restore">{{ $t("Restore note") }}</AppButton>
        </template>

        <form v-else @submit.prevent="save">
          <div class="editor-heading">
            <h2>{{ store.documents.some(d => d.id === draft?.id) ? $t('Edit note') : $t('New note') }}</h2>
            <AppButton type="submit">{{ $t("Save note") }}</AppButton>
          </div>
          <label>{{ $t("Title") }}<input v-model="draft.title" required /></label>
          <div class="field-grid">
            <label>{{ $t("URL slug") }}<input v-model="draft.slug" required /></label>
            <label>{{ $t("Type") }} <select v-model="draft.kind">
                <option value="Research Note">{{ $t("Research Note") }}</option><option value="Essay">{{ $t("Essay") }}</option><option value="Guide">{{ $t("Guide") }}</option><option value="Reference">{{ $t("Reference") }}</option>
              </select>
            </label>
            <label>{{ $t("Visibility") }} <select v-model="draft.visibility">
                <option value="private">{{ $t("Private") }}</option><option value="public">{{ $t("Public") }}</option><option value="unlisted">{{ $t("Unlisted") }}</option>
              </select>
            </label>
            <label>{{ $t("Publication date") }}<input v-model="draft.publishedAt" type="date" /></label>
          </div>
          <label>{{ $t("Summary") }}<textarea v-model="draft.summary" rows="2" /></label>
          <TagEditor v-model="draft.tags" />
          <label class="check-field"><input v-model="draft.featured" type="checkbox" /> {{ $t("Feature on homepage") }}</label>
          <label class="upload-markdown-button"><span>{{ $t("Replace content from Markdown") }}</span><input type="file" accept=".md,.markdown,text/markdown" @change="replaceContent" /></label>
          <div class="markdown-editor">
            <label>{{ $t("Markdown") }}<textarea v-model="draft.content" rows="18" :placeholder="$t('# Start writing…')" /></label>
            <section><p class="field-label">{{ $t("Preview") }}</p><MarkdownBody :content="draft.content" /></section>
          </div>
          <p class="muted-copy">{{ $t("Private notes are available in the workspace. Public notes appear in the library. Unlisted notes are reachable by their link.") }}</p>
          <div class="editor-actions">
            <AppButton type="submit">{{ $t("Save note") }}</AppButton>
            <RouterLink v-if="store.documents.some(d => d.id === draft?.id) && draft.visibility !== 'private'" :to="'/notes/' + draft.slug">{{ $t("Open reading page ↗") }}</RouterLink>
            <button v-if="store.documents.some(d => d.id === draft?.id)" type="button" class="text-action danger" @click="pendingId = draft.id">{{ $t("Move to Trash") }}</button>
          </div>
          <div v-if="pendingId" class="inline-confirm">
            <span>{{ $t("Move this note to Trash? You can restore it later.") }}</span>
            <AppButton @click="trash">{{ $t("Move to Trash") }}</AppButton>
            <button type="button" @click="pendingId = null">{{ $t("Cancel") }}</button>
          </div>
        </form>
      </section>

      <section v-else class="record-editor empty-state">
        <h2>{{ $t("Your research notebook") }}</h2>
        <p>{{ $t("Select a note or create one. Paper links are optional, and one paper can link to multiple notes.") }}</p>
      </section>
    </div>
  </div>
</template>
