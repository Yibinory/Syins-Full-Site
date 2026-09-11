<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import PublicLayout from '@/layouts/PublicLayout.vue'
import MarkdownBody from '../components/MarkdownBody.vue'
import { useWorkspaceStore } from '@/stores/workspace'
const route = useRoute(); const store = useWorkspaceStore()
const note = computed(() => store.documents.find(n => n.slug === route.params.slug && !n.trashedAt && n.visibility !== 'private'))
const readingContent = computed(() => {
  if (!note.value) return ''
  const lines = note.value.content.split('\n')
  if (lines[0]?.replace(/^#\s+/, '').trim() === note.value.title.trim() && /^#\s+/.test(lines[0])) return lines.slice(1).join('\n').trimStart()
  return note.value.content
})
</script>
<template><PublicLayout><article class="note-reading"><RouterLink to="/notes">← Notes</RouterLink><template v-if="note"><p class="section-kicker">{{ note.kind }} · {{ note.publishedAt }}</p><h1>{{ note.title }}</h1><p class="note-summary">{{ note.summary }}</p><div class="tag-list"><span v-for="tag in note.tags" :key="tag">{{ tag }}</span></div><MarkdownBody :content="readingContent" /></template><template v-else><h1>Note unavailable</h1><p>This note is private, in Trash, or no longer exists.</p></template></article></PublicLayout></template>
