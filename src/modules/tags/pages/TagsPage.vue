<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Check, Palette, Plus, Tag as TagIcon } from 'lucide-vue-next'
import DashboardPageHeader from '@/components/shared/DashboardPageHeader.vue'
import AppButton from '@/components/ui/AppButton.vue'
import { useWorkspaceStore, type WorkspaceTag } from '@/stores/workspace'

const store = useWorkspaceStore()
const selectedId = ref<number | null>(null)
const showForm = ref(false)
const notice = ref('')
const busy = ref(false)
const draft = reactive({ name: '', color: '#5C7891', description: '', parentId: null as number | null })
const selected = computed(() => store.tags.find(tag => tag.id === selectedId.value) ?? null)
const parentOptions = computed(() => store.tags.filter(tag => tag.id !== selectedId.value))

function edit(tag: WorkspaceTag) {
  selectedId.value = tag.id
  Object.assign(draft, { name: tag.name, color: tag.color, description: tag.description, parentId: tag.parentId })
  showForm.value = true
  notice.value = ''
}

function newTag() {
  selectedId.value = null
  Object.assign(draft, { name: '', color: '#5C7891', description: '', parentId: null })
  showForm.value = true
  notice.value = ''
}

async function save() {
  if (!draft.name.trim()) { notice.value = 'Enter a tag name.'; return }
  busy.value = true
  try {
    if (selected.value) await store.saveTag({ ...selected.value, name: draft.name.trim(), color: draft.color, description: draft.description.trim(), parentId: draft.parentId || null })
    else { const created = await store.createTag({ name: draft.name.trim(), color: draft.color, description: draft.description.trim(), parentId: draft.parentId || null }); selectedId.value = created.id }
    notice.value = 'Tag metadata saved.'
    showForm.value = false
  } catch { notice.value = 'The tag could not be saved. Names and colors must be valid and hierarchy cycles are not allowed.' }
  finally { busy.value = false }
}

onMounted(() => { if (!store.hydrated) store.hydrate() })
</script>

<template>
  <div>
    <DashboardPageHeader :title="$t('Tags')" :description="$t('One shared vocabulary for papers, publications and notes, with color, description and hierarchy.')"><AppButton @click="newTag"><Plus :size="15" /> {{ $t("New tag") }}</AppButton></DashboardPageHeader>
    <p v-if="notice" class="feedback" role="status">{{ $t(notice) }}</p>
    <div class="tag-management-layout">
      <section class="tag-management-list">
        <button v-for="tag in store.tags" :key="tag.id" type="button" :class="{ active: selectedId === tag.id }" @click="edit(tag)"><i :style="{ background: tag.color }" /><span><strong>{{ tag.name }}</strong><small>{{ tag.parentId ? $t('Child tag') : $t('Top-level tag') }}</small></span><Palette :size="14" /></button>
        <p v-if="!store.tags.length" class="empty-hint">{{ $t("Tags will appear here after the first paper, publication or note uses one.") }}</p>
      </section>
      <section v-if="showForm" class="record-editor tag-metadata-editor">
        <div class="editor-heading"><h2>{{ selected ? $t('Edit tag') : $t('Create tag') }}</h2><AppButton type="button" :disabled="busy" @click="save">{{ busy ? $t('Saving…') : $t('Save tag') }}</AppButton></div>
        <label>{{ $t("Name") }}<input v-model="draft.name" required /></label>
        <div class="field-grid"><label>{{ $t("Color") }}<div class="tag-color-control"><input v-model="draft.color" type="color" /><input v-model="draft.color" pattern="#[0-9A-Fa-f]{6}" /></div></label><label>{{ $t("Parent tag") }}<select v-model.number="draft.parentId"><option :value="null">{{ $t("No parent") }}</option><option v-for="tag in parentOptions" :key="tag.id" :value="tag.id">{{ tag.name }}</option></select></label></div>
        <label>{{ $t("Description") }}<textarea v-model="draft.description" rows="5" :placeholder="$t('What does this tag organize?')" /></label>
        <div class="editor-actions"><AppButton type="button" :disabled="busy" @click="save"><Check :size="14" /> {{ $t("Save metadata") }}</AppButton><button type="button" @click="showForm = false">{{ $t("Cancel") }}</button></div>
      </section>
      <section v-else class="record-editor empty-state"><TagIcon :size="26" /><h2>{{ $t("Shared research vocabulary") }}</h2><p>{{ $t("Select a tag to edit its visual identity and hierarchy, or create a new one.") }}</p><AppButton @click="newTag">{{ $t("Create tag") }}</AppButton></section>
    </div>
  </div>
</template>
