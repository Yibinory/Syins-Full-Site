<script setup lang="ts">
import LanguageSwitch from '@/components/shared/LanguageSwitch.vue'
import { Menu, Moon, Sun, X } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { useSiteContentStore } from '@/stores/siteContent'

const siteContent = useSiteContentStore()
import { useColorMode, useWindowScroll, useWindowSize } from '@vueuse/core'

const menuOpen = ref(false)
const mode = useColorMode({ modes: { light: 'light', dark: 'dark' } })
const { y } = useWindowScroll()
const { height } = useWindowSize()
const scrollProgress = computed(() => Math.min(1, y.value / Math.max(1, document.documentElement.scrollHeight - height.value)))
const toggleTheme = () => { mode.value = mode.value === 'dark' ? 'light' : 'dark' }
</script>

<template>
  <div class="public-shell">
    <div class="scroll-progress" :style="{ transform: `scaleX(${scrollProgress})` }" />
    <header class="public-nav">
      <RouterLink to="/" class="wordmark">{{ siteContent.content.name }}</RouterLink>
      <nav class="desktop-nav" :aria-label="$t('Main navigation')">
        <RouterLink :to="{ path: '/', hash: '#research' }"><small>01</small> {{ $t("Research") }}</RouterLink>
        <RouterLink to="/publications"><small>02</small> {{ $t("Publications") }}</RouterLink>
        <RouterLink to="/notes"><small>03</small> {{ $t("Notes") }}</RouterLink>
        <RouterLink to="/papers"><small>04</small> {{ $t("Recommended") }}</RouterLink>
        <RouterLink to="/tools"><small>05</small> {{ $t("Tools") }}</RouterLink>
        <span class="nav-divider" />
        <a :href="siteContent.content.scholarUrl">{{ $t("Scholar ↗") }}</a>
        <a :href="siteContent.content.githubUrl">{{ $t("GitHub ↗") }}</a>
        <button class="theme-button" type="button" :aria-label="$t('Toggle color theme')" @click="toggleTheme">
          <Sun v-if="mode === 'dark'" :size="16" />
          <Moon v-else :size="16" />
        </button>
      </nav>
      <LanguageSwitch />
      <button class="mobile-menu-button" type="button" :aria-label="$t('Open navigation')" @click="menuOpen = !menuOpen">
        <X v-if="menuOpen" :size="21" />
        <Menu v-else :size="21" />
      </button>
    </header>
    <div v-if="menuOpen" class="mobile-nav">
      <RouterLink :to="{ path: '/', hash: '#research' }" @click="menuOpen = false">{{ $t("Research") }}</RouterLink>
      <RouterLink to="/publications" @click="menuOpen = false">{{ $t("Publications") }}</RouterLink>
      <RouterLink to="/notes" @click="menuOpen = false">{{ $t("Notes") }}</RouterLink>
      <RouterLink to="/papers" @click="menuOpen = false">{{ $t("Recommended papers") }}</RouterLink>
      <RouterLink to="/tools" @click="menuOpen = false">{{ $t("Tools") }}</RouterLink>
      <RouterLink to="/dashboard" @click="menuOpen = false">{{ $t("Research OS") }}</RouterLink>
    </div>
    <main><slot /></main>
    <footer class="public-footer">
      <div>
        <p class="footer-name">{{ siteContent.content.name }}</p>
        <p>{{ $t("Medical image analysis · Generative modeling") }}</p>
      </div>
      <div class="footer-right">
        <RouterLink to="/dashboard">{{ $t("Research OS") }}</RouterLink>
        <p>{{ $t("© 2026 · Last updated Sep 2026") }}</p>
      </div>
    </footer>
  </div>
</template>
