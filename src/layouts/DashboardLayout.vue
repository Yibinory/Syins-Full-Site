<script setup lang="ts">
import { BookOpenText, Boxes, ChevronLeft, FileText, Gauge, LayoutTemplate, Newspaper, Menu, Network, PanelLeftClose, Search, Settings, X } from 'lucide-vue-next'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const open = ref(false)
const collapsed = ref(false)
const router = useRouter()
const auth = useAuthStore()
const nav = [
  { label: 'Overview', to: '/dashboard', icon: Gauge },
  { group: 'PUBLIC SITE', label: 'Site content', to: '/dashboard/content', icon: LayoutTemplate },
  { label: 'Publications', to: '/dashboard/publications', icon: Newspaper },
  { group: 'WORKSPACE', label: 'Recommended papers', to: '/dashboard/papers', icon: BookOpenText },
  { label: 'Documents', to: '/dashboard/docs', icon: FileText },
  { group: 'INFRASTRUCTURE', label: 'Servers', to: '/dashboard/servers', icon: Boxes },
  { label: 'VPN', to: '/dashboard/vpn', icon: Network },
  { group: 'SYSTEM', label: 'Settings', to: '/dashboard/settings', icon: Settings },
]
function logout() { auth.logout(); router.push('/') }
</script>

<template>
  <div class="dashboard-shell" :class="{ 'is-collapsed': collapsed, 'nav-open': open }">
    <aside class="dashboard-sidebar">
      <div class="dashboard-brand"><div class="brand-mark">SY</div><div class="brand-text"><strong>Research OS</strong><span>Syins Yibinory</span></div><button aria-label="Close navigation" @click="open = false"><X :size="18" /></button></div>
      <nav class="dashboard-nav"><template v-for="item in nav" :key="item.to"><p v-if="item.group" class="nav-group">{{ item.group }}</p><RouterLink :to="item.to" @click="open = false"><component :is="item.icon" :size="17" /><span>{{ item.label }}</span></RouterLink></template></nav>
      <div class="sidebar-footer"><RouterLink to="/"><ChevronLeft :size="16" /><span>Public site</span></RouterLink><button @click="logout"><span class="user-avatar">SY</span><span class="user-copy"><strong>Syins Yibinory</strong><small>Sign out</small></span></button></div>
    </aside>
    <div class="dashboard-main">
      <header class="dashboard-topbar"><button class="mobile-dashboard-menu" aria-label="Open navigation" @click="open = true"><Menu :size="19" /></button><button class="collapse-button" aria-label="Collapse sidebar" @click="collapsed = !collapsed"><PanelLeftClose :size="17" /></button><button class="command-search"><Search :size="15" /><span>Search workspace</span><kbd>⌘ K</kbd></button><span class="sync-state"><i /> Connected workspace</span></header>
      <main class="dashboard-content"><RouterView /></main>
    </div>
    <button v-if="open" class="dashboard-overlay" aria-label="Close navigation" @click="open = false" />
  </div>
</template>
