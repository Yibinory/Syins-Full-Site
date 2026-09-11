<script setup lang="ts">withDefaults(defineProps<{ status?: 'online' | 'offline' | 'warning' }>(), { status: 'online' })</script>
<template><span class="status-dot" :class="`status-dot--${status}`" aria-hidden="true" /></template>

