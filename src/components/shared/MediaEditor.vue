<script setup lang="ts">
import { ref } from 'vue'
import { importMedia, deleteMedia } from '@/services/mediaLibrary'
import ResearchMedia from './ResearchMedia.vue'
export interface EditableMedia { title: string; mediaType: 'image' | 'video' | 'interactive'; mediaUrl: string; mediaAlt: string; caption: string; mediaAssetId?: string }
const props = defineProps<{ modelValue: EditableMedia }>()
const emit = defineEmits<{ 'update:modelValue': [EditableMedia] }>()
const busy = ref(false); const message = ref(''); const confirmClear = ref(false)
async function upload(event: Event) {
  const input = event.target as HTMLInputElement; const file = input.files?.[0]; if (!file) return
  const target = props.modelValue
  busy.value = true; message.value = ''
  try { const asset = await importMedia(file); if (props.modelValue !== target) { await deleteMedia(asset.id); return } emit('update:modelValue', { ...props.modelValue, mediaAssetId: asset.id, mediaType: asset.kind, mediaUrl: '', caption: props.modelValue.caption }); message.value = `Imported ${file.name}.` }
  catch (error) { message.value = error instanceof Error ? error.message : 'Import failed. The previous visual has been kept.' }
  finally { busy.value = false; input.value = '' }
}
function clear() { emit('update:modelValue', { ...props.modelValue, mediaAssetId: undefined, mediaUrl: '' }); confirmClear.value = false; message.value = 'Visual removed from this record. Unused files can be deleted in Settings after saving.' }
</script>
<template><section class="media-editor"><h3>Research visual</h3><div class="field-grid"><label>Display type<select :disabled="busy" v-model="modelValue.mediaType" @change="emit('update:modelValue', { ...modelValue, mediaAssetId: undefined, mediaUrl: '' })"><option value="image">Image / SVG</option><option value="video">Video</option><option value="interactive">HTML / Vue interactive</option></select></label><label>Upload or replace<input type="file" accept=".html,.htm,.vue,.zip,.png,.jpg,.jpeg,.webp,.svg,.gif,.avif,.mp4,.webm" :disabled="busy" @change="upload" /></label></div><p class="muted-copy">HTML, Vue component, or ZIP with index.html / App.vue; maximum 25 MB. Vue supports local components and the Vue runtime. For other dependencies, upload the built HTML package. Everything runs locally inside an isolated frame.</p><p class="example-downloads">Examples: <a href="/examples/interactive-demo.html" download>HTML file</a> · <a href="/examples/ResearchDemo.vue" download>Vue component</a> · <a href="/examples/vue-demo.zip" download>Vue ZIP</a></p><label v-if="modelValue.mediaType !== 'interactive' && !modelValue.mediaAssetId">Or use a media URL<input v-model="modelValue.mediaUrl" placeholder="/images/figure.svg or https://…" /></label><div class="field-grid"><label>Accessible description<input v-model="modelValue.mediaAlt" /></label><label>Caption<input v-model="modelValue.caption" /></label></div><p v-if="busy || message" class="feedback" role="status">{{ busy ? 'Preparing interactive visual…' : message }}</p><ResearchMedia v-if="modelValue.mediaAssetId || modelValue.mediaUrl" :project="modelValue" /><button v-if="modelValue.mediaAssetId || modelValue.mediaUrl" type="button" class="text-action danger" @click="confirmClear = true">Clear visual</button><div v-if="confirmClear" class="inline-confirm"><span>Remove this visual from the record?</span><button type="button" @click="clear">Clear</button><button type="button" @click="confirmClear = false">Cancel</button></div></section></template>
