<script setup lang="ts">
import { useWorkspaceStore } from '@/stores/workspace'
import { useSiteContentStore } from '@/stores/siteContent'
const siteContent = useSiteContentStore()
import LanguageSwitch from '@/components/shared/LanguageSwitch.vue'
import { BookOpenText, Boxes, ChevronLeft, ExternalLink, FileText, Gauge, LayoutTemplate, Newspaper, Menu, Network, PanelLeftClose, Search, Settings, Tags, X } from 'lucide-vue-next'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useIntegrationsStore } from '@/stores/integrations'

const open = ref(false)
const collapsed = ref(false)
const router = useRouter()
const auth = useAuthStore()
const integrations = useIntegrationsStore()
const nav = [
  { label: 'Overview', to: '/dashboard', icon: Gauge },
  { group: 'PUBLIC SITE', label: 'Site content', to: '/dashboard/content', icon: LayoutTemplate },
  { label: 'Publications', to: '/dashboard/publications', icon: Newspaper },
  { group: 'WORKSPACE', label: 'Recommended papers', to: '/dashboard/papers', icon: BookOpenText },
  { label: 'Documents', to: '/dashboard/docs', icon: FileText },
  { group: 'INFRASTRUCTURE', label: 'Servers', to: '/dashboard/servers', icon: Boxes },
  { label: 'Dashboard pages', to: '/dashboard/integrations', icon: ExternalLink },
  { label: 'Tags', to: '/dashboard/tags', icon: Tags },
  { group: 'SYSTEM', label: 'Settings', to: '/dashboard/settings', icon: Settings },
]
async function logout() { await auth.logout(); await useWorkspaceStore().hydrate(true); router.push('/') }
onMounted(() => integrations.hydrate())
</script>

<template>
  <div class="dashboard-shell" :class="{ 'is-collapsed': collapsed, 'nav-open': open }">
    <aside class="dashboard-sidebar">
      <div class="dashboard-brand"><div class="brand-mark">{{ siteContent.localized.name.slice(0, 2).toUpperCase() }}</div><div class="brand-text"><strong>{{ $t("Research OS") }}</strong><span>{{ siteContent.localized.name }}</span></div><button :aria-label="$t('Close navigation')" @click="open = false"><X :size="18" /></button></div>
      <nav class="dashboard-nav"><template v-for="item in nav" :key="item.to"><p v-if="item.group" class="nav-group">{{ $t(item.group) }}</p><RouterLink :to="item.to" @click="open = false"><component :is="item.icon" :size="17" /><span>{{ $t(item.label) }}</span></RouterLink></template></nav>
      <div class="sidebar-footer"><RouterLink to="/"><ChevronLeft :size="16" /><span>{{ $t("Public site") }}</span></RouterLink><button @click="logout"><span class="user-avatar">{{ siteContent.localized.name.slice(0, 2).toUpperCase() }}</span><span class="user-copy"><strong>{{ siteContent.localized.name }}</strong><small>{{ $t("Sign out") }}</small></span></button></div>
    </aside>
    <div class="dashboard-main">
      <header class="dashboard-topbar"><LanguageSwitch /><button class="mobile-dashboard-menu" :aria-label="$t('Open navigation')" @click="open = true"><Menu :size="19" /></button><button class="collapse-button" :aria-label="$t('Collapse sidebar')" @click="collapsed = !collapsed"><PanelLeftClose :size="17" /></button><button class="command-search"><Search :size="15" /><span>{{ $t("Search workspace") }}</span><kbd>⌘ K</kbd></button><span class="sync-state"><i /> {{ $t("Connected workspace") }}</span></header>
      <main class="dashboard-content"><RouterView /></main>
    </div>
    <button v-if="open" class="dashboard-overlay" :aria-label="$t('Close navigation')" @click="open = false" />
  </div>
</template>
