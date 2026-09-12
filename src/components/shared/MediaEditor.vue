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
<template><section class="media-editor"><h3>{{ $t("Research visual") }}</h3><div class="field-grid"><label>{{ $t("Display type") }}<select :disabled="busy" v-model="modelValue.mediaType" @change="emit('update:modelValue', { ...modelValue, mediaAssetId: undefined, mediaUrl: '' })"><option value="image">{{ $t("Image / SVG") }}</option><option value="video">{{ $t("Video") }}</option><option value="interactive">{{ $t("HTML / Vue interactive") }}</option></select></label><label>{{ $t("Upload or replace") }}<input type="file" accept=".html,.htm,.vue,.zip,.png,.jpg,.jpeg,.webp,.svg,.gif,.avif,.mp4,.webm" :disabled="busy" @change="upload" /></label></div><p class="muted-copy">{{ $t("HTML, Vue component, or ZIP with index.html / App.vue; maximum 25 MB. Vue supports local components and the Vue runtime. For other dependencies, upload the built HTML package. Everything runs locally inside an isolated frame.") }}</p><p class="example-downloads">{{ $t("Examples:") }} <a href="/examples/interactive-demo.html" download>{{ $t("HTML file") }}</a> · <a href="/examples/ResearchDemo.vue" download>{{ $t("Vue component") }}</a> · <a href="/examples/vue-demo.zip" download>{{ $t("Vue ZIP") }}</a></p><label v-if="modelValue.mediaType !== 'interactive' && !modelValue.mediaAssetId">{{ $t("Or use a media URL") }}<input v-model="modelValue.mediaUrl" :placeholder="$t('/images/figure.svg or https://…')" /></label><div class="field-grid"><label>{{ $t("Accessible description") }}<input v-model="modelValue.mediaAlt" /></label><label>{{ $t("Caption") }}<input v-model="modelValue.caption" /></label></div><p v-if="busy || message" class="feedback" role="status">{{ busy ? $t('Preparing interactive visual…') : message }}</p><ResearchMedia v-if="modelValue.mediaAssetId || modelValue.mediaUrl" :project="modelValue" /><button v-if="modelValue.mediaAssetId || modelValue.mediaUrl" type="button" class="text-action danger" @click="confirmClear = true">{{ $t("Clear visual") }}</button><div v-if="confirmClear" class="inline-confirm"><span>{{ $t("Remove this visual from the record?") }}</span><button type="button" @click="clear">{{ $t("Clear") }}</button><button type="button" @click="confirmClear = false">{{ $t("Cancel") }}</button></div></section></template>
