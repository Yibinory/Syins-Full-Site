<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
marked.setOptions({ gfm: true, breaks: false })
const props = defineProps<{ content: string }>()
const html = computed(() => DOMPurify.sanitize(marked.parse(props.content, { async: false }) as string, { FORBID_TAGS: ['style', 'iframe', 'form', 'input', 'button'], FORBID_ATTR: ['style'] }))
</script>
<template><div class="markdown-body" v-html="html" /></template>
