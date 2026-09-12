<script setup lang="ts">
import { locale, setLocale } from '@/i18n'
</script>
<template><button class="language-switch" type="button" :aria-label="locale === 'en' ? '切换为中文' : 'Switch to English'" @click="setLocale(locale === 'en' ? 'zh' : 'en')"><span :class="{ active: locale === 'zh' }">中</span><span aria-hidden="true">/</span><span :class="{ active: locale === 'en' }">EN</span></button></template>
