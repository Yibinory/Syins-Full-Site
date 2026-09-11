<script setup lang="ts">defineProps<{ eyebrow?: string; title: string; description?: string }>()</script>
<template><header class="dashboard-page-header"><div><p v-if="eyebrow">{{ eyebrow }}</p><h1>{{ title }}</h1><span v-if="description">{{ description }}</span></div><div class="page-actions"><slot /></div></header></template>

