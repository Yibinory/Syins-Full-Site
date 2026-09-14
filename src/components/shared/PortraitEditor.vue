<script setup lang="ts">
import { ref } from 'vue'
import { http } from '@/services/http'
import { useSiteContentStore } from '@/stores/siteContent'
const store = useSiteContentStore()
const busy = ref(false)
const error = ref('')
async function upload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  error.value = ''
  if (!/\.(png|jpe?g|webp|gif|avif|svg)$/i.test(file.name) || file.size > 25 * 1024 * 1024) {
    error.value = 'Choose an image up to 25 MB.'
    input.value = ''
    return
  }
  busy.value = true
  try {
    const form = new FormData()
    form.append('upload', file)
    const { data } = await http.post<{ id: string; sourceUrl: string }>('/media/', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    store.content.portraitAssetId = data.id
    store.content.portraitUrl = data.sourceUrl
  } catch { error.value = 'Portrait upload failed. Please try again.' }
  finally { busy.value = false; input.value = '' }
}
function clear() { store.content.portraitAssetId = null; store.content.portraitUrl = '' }
</script>
<template>
  <section class="portrait-editor">
    <h3>{{ $t('Homepage portrait') }}</h3>
    <p>{{ $t('The same portrait is used in Chinese and English. Save changes to publish it.') }}</p>
    <img v-if="store.content.portraitUrl" :src="store.content.portraitUrl" :alt="$t('Homepage portrait')" />
    <label>{{ $t('Upload or replace') }}<input type="file" accept=".png,.jpg,.jpeg,.webp,.gif,.avif,.svg" :disabled="busy" @change="upload" /></label>
    <p v-if="busy" role="status">{{ $t('Uploading…') }}</p>
    <p v-if="error" role="alert">{{ $t(error) }}</p>
    <button v-if="store.content.portraitAssetId" type="button" :disabled="busy" @click="clear">{{ $t('Remove portrait') }}</button>
    <small>{{ $t('Choose an image up to 25 MB.') }}</small>
  </section>
</template>
<style scoped>
.portrait-editor { padding: 20px; border: 1px solid var(--border, #dce4e4); border-radius: 10px; margin-bottom: 24px; }
.portrait-editor p, .portrait-editor small { display: block; color: var(--text-muted, #647780); margin: 10px 0; }
.portrait-editor img { width: 160px; height: 200px; object-fit: cover; border-radius: 6px; margin: 12px 0; }
.portrait-editor button { margin-top: 12px; }
</style>
