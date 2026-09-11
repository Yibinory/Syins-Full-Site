<script setup lang="ts">
withDefaults(defineProps<{ variant?: 'primary' | 'secondary' | 'ghost'; type?: 'button' | 'submit' }>(), { variant: 'primary', type: 'button' })
</script>

<template><button :type="type" class="ui-button" :class="`ui-button--${variant}`"><slot /></button></template>

