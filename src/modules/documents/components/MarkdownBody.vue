<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '@/services/markdown'
import 'katex/dist/katex.min.css'
const props = defineProps<{ content: string }>()
const html = computed(() => renderMarkdown(props.content))
</script>
<template><div class="markdown-body" v-html="html" /></template>
<style>
.markdown-body .katex { font-size: 1.08em; }
.markdown-body .katex-display { max-width: 100%; overflow-x: auto; overflow-y: hidden; padding: .5em 0; }
.markdown-body .katex-display > .katex { white-space: nowrap; }
</style>
