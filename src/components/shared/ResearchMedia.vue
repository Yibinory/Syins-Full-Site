<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue'
import { getMedia } from '@/services/mediaLibrary'
const props = defineProps<{ project: { title: string; mediaType: 'image' | 'video' | 'interactive'; mediaUrl: string; mediaAlt: string; caption: string; mediaAssetId?: string } }>()
const failed = ref(false); const loading = ref(false); const url = ref(''); const html = ref(''); let objectURL = ''; let generation = 0
function release() { if (objectURL) URL.revokeObjectURL(objectURL); objectURL = '' }
watch(() => [props.project.mediaUrl, props.project.mediaType, props.project.mediaAssetId], async () => {
  const current = ++generation; release(); failed.value = false; html.value = ''; url.value = props.project.mediaUrl; loading.value = false
  if (!props.project.mediaAssetId) return
  loading.value = true
  try { const asset = await getMedia(props.project.mediaAssetId); if (current !== generation) return; if (!asset) { failed.value = true; return }
    if (props.project.mediaType === 'interactive') {
      const { compileInteractive } = await import('@/services/interactiveCompiler')
      const file = new File([asset.source], asset.name, { type: asset.contentType || 'application/octet-stream' })
      const content = await compileInteractive(file)
      if (current === generation) html.value = content
    }
    else { objectURL = URL.createObjectURL(asset.rendered); url.value = objectURL }
  } catch { if (current === generation) failed.value = true } finally { if (current === generation) loading.value = false }
}, { immediate: true })
onBeforeUnmount(() => { generation++; release() })
</script>
<template><figure class="research-visual project-media"><div class="project-media-frame" :class="{ 'interactive-frame': project.mediaType === 'interactive' }"><p v-if="loading" class="project-media-empty">Loading visual…</p><p v-else-if="failed || (!url && !html)" class="project-media-empty">Research figure coming soon</p><iframe v-else-if="project.mediaType === 'interactive'" :srcdoc="html" :title="project.mediaAlt || project.title" sandbox="allow-scripts" referrerpolicy="no-referrer" /><video v-else-if="project.mediaType === 'video'" :key="url" :src="url" :aria-label="project.mediaAlt || project.title" controls playsinline preload="metadata" @error="failed = true" /><img v-else :src="url" :alt="project.mediaAlt || project.title" loading="lazy" @error="failed = true" /></div><figcaption v-if="project.caption">{{ project.caption }}</figcaption></figure></template>
