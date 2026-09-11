import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import HomePage from '@/modules/profile/pages/HomePage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomePage },
    { path: '/research', redirect: { path: '/', hash: '#research' } },
    { path: '/publications', name: 'publications', component: () => import('@/modules/publications/pages/PublicationsPage.vue') },
    { path: '/notes', name: 'notes', component: () => import('@/modules/documents/pages/NotesPage.vue') },
    { path: '/notes/:slug', name: 'note-detail', component: () => import('@/modules/documents/pages/NoteDetailPage.vue') },
    { path: '/about', redirect: '/notes' },
    { path: '/login', name: 'login', component: () => import('@/modules/accounts/pages/LoginPage.vue'), meta: { publicOnly: true } },
    {
      path: '/dashboard',
      component: () => import('@/layouts/DashboardLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'dashboard', component: () => import('@/modules/dashboard/pages/OverviewPage.vue') },
        { path: 'content', name: 'site-content', component: () => import('@/modules/dashboard/pages/SiteContentPage.vue') },
        { path: 'papers', name: 'papers', component: () => import('@/modules/papers/pages/PapersPage.vue') },
        { path: 'servers', name: 'servers', component: () => import('@/modules/servers/pages/ServersPage.vue') },
        { path: 'research', redirect: '/dashboard/content' },
        { path: 'publications', name: 'publication-manager', component: () => import('@/modules/publications/pages/PublicationManagerPage.vue') },
        { path: 'docs', name: 'docs', component: () => import('@/modules/documents/pages/DocumentsPage.vue') },
        { path: 'vpn', name: 'vpn', component: () => import('@/modules/dashboard/pages/ModulePlaceholderPage.vue'), props: { title: 'VPN', copy: 'Read-only 3x-ui integration is reserved for Phase 2.' } },
        { path: 'settings', name: 'settings', component: () => import('@/modules/dashboard/pages/SettingsPage.vue') },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: (to) => to.hash ? { el: to.hash, top: 90 } : { top: 0 },
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) return { name: 'login', query: { redirect: to.fullPath } }
  if (to.meta.publicOnly && auth.isAuthenticated) return { name: 'dashboard' }
})

export default router
