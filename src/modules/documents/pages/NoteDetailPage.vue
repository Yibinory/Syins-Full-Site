<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import PublicLayout from '@/layouts/PublicLayout.vue'
import MarkdownBody from '../components/MarkdownBody.vue'
import { documentsApi } from '../api'
import { useAuthStore } from '@/stores/auth'
import { useWorkspaceStore, type Document } from '@/stores/workspace'

const route = useRoute()
const auth = useAuthStore()
const store = useWorkspaceStore()
const note = ref<Document | null>(null)
const loading = ref(true)

const readingContent = computed(() => {
  if (!note.value) return ''
  const lines = note.value.content.split('\n')
  if (lines[0]?.replace(/^#\s+/, '').trim() === note.value.title.trim() && /^#\s+/.test(lines[0])) return lines.slice(1).join('\n').trimStart()
  return note.value.content
})

async function loadNote() {
  loading.value = true
  note.value = null
  const slug = String(route.params.slug)
  const local = store.documents.find(item => item.slug === slug)
  if (local && (auth.isAuthenticated || local.visibility !== 'private')) note.value = local
  try {
    const response = await documentsApi.getPublic(slug)
    note.value = { ...(local ?? {}), ...response.data } as Document
  } catch {
    // Keep the same page for missing notes and unauthenticated private notes.
  } finally {
    loading.value = false
  }
}

onMounted(loadNote)
watch(() => route.params.slug, loadNote)
</script>

<template>
  <PublicLayout>
    <article class="note-reading">
      <RouterLink to="/notes">{{ $t("← Notes") }}</RouterLink>
      <p v-if="loading" class="public-paper-state">{{ $t("Loading note…") }}</p>
      <template v-else-if="note">
        <p class="section-kicker">{{ $t(note.kind) }} · {{ note.publishedAt || $t('Undated') }}</p>
        <h1>{{ note.title }}</h1>
        <p class="note-summary">{{ note.summary }}</p>
        <div class="tag-list"><span v-for="tag in note.tags" :key="tag">{{ tag }}</span></div>
        <MarkdownBody :content="readingContent" />
      </template>
      <template v-else>
        <h1>{{ auth.isAuthenticated ? $t('Note unavailable') : $t('This note may be private') }}</h1>
        <p>{{ auth.isAuthenticated ? $t('This note is in Trash or no longer exists.') : $t('Sign in to read private notes, or return to the public notes library.') }}</p>
        <RouterLink v-if="!auth.isAuthenticated" class="paper-note-login" :to="{ path: '/login', query: { redirect: route.fullPath } }">{{ $t("Sign in to continue →") }}</RouterLink>
      </template>
    </article>
  </PublicLayout>
</template>
