<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { http } from '@/services/http'
import AppButton from '@/components/ui/AppButton.vue'
interface Ports { appPort: number; databasePort: number | null }
interface Job { id?: string; status: string; message: string; requested?: Ports; previous?: Ports }
interface State { online: boolean; current: Ports | null; job: Job | null; error?: string }
const state = ref<State | null>(null)
const appPort = ref(8080)
const databasePort = ref(5432)
const publishDatabase = ref(false)
const pending = ref(false)
const notice = ref('')
const target = ref('')
const forbidden = ref(false)
let submittedId = ''
let timer: ReturnType<typeof setInterval> | undefined
let initialized = false
const busy = computed(() => pending.value || ['checking', 'applying'].includes(state.value?.job?.status || ''))
async function refresh() {
  try {
    const response = await http.get<State>('/settings/deployment/')
    state.value = response.data
    if (!initialized && state.value.current) {
      appPort.value = state.value.current.appPort
      publishDatabase.value = state.value.current.databasePort !== null
      databasePort.value = state.value.current.databasePort ?? 5432
      initialized = true
    }
    const job = state.value.job
    if (job && (!submittedId || job.id === submittedId) && !['checking', 'applying', 'queued'].includes(job.status)) pending.value = false
  } catch (error: any) {
    if (error.response?.status === 403) forbidden.value = true
    else if (pending.value) notice.value = 'The service is restarting. Open the new address, or return here if the change is rolled back.'
  }
}
async function apply() {
  notice.value = ''
  const ports = { appPort: Number(appPort.value), databasePort: publishDatabase.value ? Number(databasePort.value) : null }
  try {
    pending.value = true
    const response = await http.post<{ id: string }>('/settings/deployment/', ports)
    submittedId = response.data.id
    state.value = { ...state.value!, job: { id: response.data.id, status: 'queued', message: 'Port change queued.' } }
    const url = new URL(window.location.href)
    url.port = String(ports.appPort)
    target.value = url.href
    notice.value = 'Port change queued.'
  } catch (error: any) {
    pending.value = false
    notice.value = error.response?.data?.detail || 'Unable to request this port change. Check the values and manager status.'
  }
}
onMounted(() => { refresh(); timer = setInterval(refresh, 2500) })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>
<template>
  <section v-if="!forbidden" class="record-editor settings-wide deployment-settings">
    <h2>{{ $t('Deployment ports') }}</h2>
    <p>{{ $t('Changes are applied by the host deployment manager and briefly restart services. Failed changes restore the previous configuration.') }}</p>
    <p>{{ $t('Manager status') }}: <strong>{{ state?.online ? $t('Online') : $t('Offline') }}</strong></p>
    <p v-if="!state?.online">{{ $t('Run on the deployment host:') }} <code>python3 scripts/deployment_manager.py start</code> · Windows: <code>py -3 scripts/deployment_manager.py start</code></p>
    <p v-if="state?.current">{{ $t('Current ports') }}: {{ $t('Website') }} {{ state.current.appPort }} · PostgreSQL {{ state.current.databasePort ?? $t('Not published') }}</p>
    <form @submit.prevent="apply">
      <label>{{ $t('Website port') }}<input v-model.number="appPort" type="number" min="1024" max="65535" required :disabled="busy" /></label>
      <label class="deployment-checkbox"><input v-model="publishDatabase" type="checkbox" :disabled="busy" />{{ $t('Allow database clients on this host only') }}</label>
      <label v-if="publishDatabase">{{ $t('Database port') }}<input v-model.number="databasePort" type="number" min="1024" max="65535" required :disabled="busy" /></label>
      <p>{{ $t('DNS, HTTPS proxies and firewall rules are not changed. If using a reverse proxy, keep using your domain and update its upstream port separately.') }}</p>
      <AppButton type="submit" :disabled="busy || !state?.online || !!state?.error">{{ $t('Apply ports and restart services') }}</AppButton>
    </form>
    <p v-if="notice" role="status">{{ $t(notice) }}</p>
    <p v-if="state?.job" role="status">{{ $t('Last change') }}: {{ $t(state.job.message) }}</p>
    <p v-if="state?.error" role="alert">{{ $t(state.error) }}</p>
    <p v-if="target"><a :href="target" target="_blank" rel="noopener">{{ $t('Open new direct address') }} ↗</a> · <a :href="'/dashboard/settings'">{{ $t('Return to this address') }}</a></p>
    <p v-if="state?.job?.status === 'recovery_required' || state?.error"><code>python3 scripts/deployment_manager.py recover</code></p>
  </section>
</template>
<style scoped>
.deployment-settings form { display: grid; gap: 16px; max-width: 620px; }
.deployment-settings p { font-size: .78rem; line-height: 1.7; color: #65767d; }
.deployment-settings code { overflow-wrap: anywhere; }
.deployment-settings a { color: #365f70; text-decoration: underline; text-underline-offset: 3px; }
.deployment-settings .deployment-checkbox { display: flex; align-items: center; gap: 10px; }
.deployment-checkbox input { width: auto; min-height: auto; }
</style>
