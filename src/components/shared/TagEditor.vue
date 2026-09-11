<script setup lang="ts">
import { ref } from 'vue'
import { normalizeTags } from '@/stores/workspace'
const props = defineProps<{ modelValue: string[]; label?: string }>()
const emit = defineEmits<{ 'update:modelValue': [string[]] }>()
const draft = ref('')
function add() { emit('update:modelValue', normalizeTags([...props.modelValue, ...draft.value.split(/[,，]/)])); draft.value = '' }
function rename(index: number, event: Event) { const next = [...props.modelValue]; next[index] = (event.target as HTMLInputElement).value; emit('update:modelValue', normalizeTags(next)) }
</script>
<template><div class="tag-editor"><span class="field-label">{{ label || 'Tags' }}</span><div class="editable-tags"><span v-for="(tag, index) in modelValue" :key="tag"><input :value="tag" :aria-label="`Rename tag ${tag}`" @change="rename(index, $event)" /><button type="button" :aria-label="`Remove tag ${tag}`" @click="emit('update:modelValue', modelValue.filter((_, i) => i !== index))">×</button></span></div><div class="inline-controls"><input v-model="draft" placeholder="Add tags, separated by commas" aria-label="New tags" @keydown.enter.prevent="add" /><button type="button" class="text-action" @click="add">Add tags</button></div></div></template>
