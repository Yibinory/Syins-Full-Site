import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { t } from './i18n'
import router from './router'
import { useAuthStore } from './stores/auth'
import { useSiteContentStore } from './stores/siteContent'
import { useWorkspaceStore } from './stores/workspace'
import './styles/main.css'
import './styles/visual-polish.css'

const app = createApp(App)
app.config.globalProperties.$t = t
const pinia = createPinia()
app.use(pinia)

async function bootstrap() {
  const auth = useAuthStore(pinia)
  await auth.hydrate()
  await Promise.all([useSiteContentStore(pinia).hydrate(), useWorkspaceStore(pinia).hydrate()])
  app.use(router)
  await router.isReady()
  app.mount('#app')
}

bootstrap()
