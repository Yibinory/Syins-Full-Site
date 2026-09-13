<script setup lang="ts">
import { formatCapacity } from '@/services/capacity'
import { t } from '@/i18n'
import { Box, Cpu, Plus, RefreshCw, ServerCog, ShieldCheck, Wifi } from 'lucide-vue-next'
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import DashboardPageHeader from '@/components/shared/DashboardPageHeader.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import StatusDot from '@/components/ui/StatusDot.vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { serversApi, type ServerMetric } from '../api'
import type { Server } from '../data'

const store = useWorkspaceStore()
const { servers } = storeToRefs(store)
const showDemo = ref(false)
const liveServers = computed(() => servers.value.filter(server => server.provider !== 'mock'))
const visibleServers = computed(() => showDemo.value ? servers.value : liveServers.value)
const saving = ref(false)
const editingId = ref<number | null>(null)
const onlineCount = computed(() => liveServers.value.filter(server => server.status === 'online' && server.enabled !== false).length)
const gpuCount = computed(() => liveServers.value.reduce((count, server) => count + server.gpus.length, 0))
const containerCount = computed(() => liveServers.value.reduce((count, server) => count + server.containers, 0))
const primaryServer = computed(() => liveServers.value.find(server => server.isPrimary) ?? liveServers.value[0] ?? null)
const selectedServerId = ref<number | null>(null)
const selectedServer = computed(() => servers.value.find(server => server.id === selectedServerId.value) ?? primaryServer.value)
const metrics = ref<ServerMetric[]>([])
const intervalSeconds = ref(30)
const notice = ref('')
const busy = ref(false)
const showAdd = ref(false)
let timer: ReturnType<typeof setInterval> | undefined

const draft = reactive({
  name: '', hostname: '', ip: '', port: 22, username: '', password: '', description: '', location: '', os: '',
  provider: 'ssh', isPrimary: false, capabilities: 'SSH, Docker, Monitoring',
})

function barWidth(value: number) {
  return Math.min(100, Math.max(0, value || 0)) + '%'
}

function metricPercent(metric: ServerMetric, kind: 'cpu' | 'memory' | 'disk') {
  if (kind === 'cpu') return metric.cpu
  const value = metric[kind]
  return value.total ? value.used / value.total * 100 : 0
}

function chartPoints(kind: 'cpu' | 'memory' | 'disk') {
  const values = metrics.value.map(metric => metricPercent(metric, kind))
  if (!values.length) return ''
  const width = 480
  const height = 132
  const padding = 8
  return values.map((value, index) => {
    const x = values.length === 1 ? width / 2 : padding + (index / (values.length - 1)) * (width - padding * 2)
    const y = height - padding - (Math.min(100, Math.max(0, value)) / 100) * (height - padding * 2)
    return x.toFixed(1) + ',' + y.toFixed(1)
  }).join(' ')
}

async function loadMetrics(server = selectedServer.value) {
  if (!server) return
  metrics.value = []
  if (server.provider === 'mock') return
  try {
    const result = await serversApi.metrics(server.id)
    if (selectedServer.value?.id === server.id) metrics.value = result.data.results
  }
  catch { metrics.value = [] }
}

async function refresh() {
  if (busy.value) return
  busy.value = true
  try {
    await store.refreshServers()
    if (!selectedServerId.value) selectedServerId.value = primaryServer.value?.id ?? null
    await loadMetrics()
    const failed = liveServers.value.filter(server => server.enabled !== false && server.status !== 'online').length
    notice.value = failed ? `${failed} host(s) could not be refreshed. See the connection details below.` : 'Live host snapshots refreshed.'
  } catch { notice.value = 'The host inventory could not be refreshed.' }
  finally { busy.value = false }
}

function stopPolling() {
  if (timer) clearInterval(timer)
  timer = undefined
}

function startPolling() {
  stopPolling()
  if (intervalSeconds.value > 0) timer = setInterval(refresh, intervalSeconds.value * 1000)
}

async function testConnection(server: Server) {
  notice.value = 'Testing connection to ' + server.name + '…'
  try {
    const result = await serversApi.testConnection(server.id)
    const hostKeyNeedsTrust = result.data.status === 'host_key_required' || result.data.status === 'host_key_mismatch'
    if (hostKeyNeedsTrust && result.data.fingerprint && window.confirm(t('Trust this SSH host key?') + '\n\n' + result.data.fingerprint)) {
      const trusted = await serversApi.trustHost(server.id, result.data.fingerprint)
      if (trusted.data.accepted) {
        Object.assign(server, trusted.data.server)
        await refresh()
      }
      notice.value = trusted.data.accepted ? (servers.value.find(item => item.id === server.id)?.lastError || 'Host key trusted; metrics refreshed.') : trusted.data.message
      return
    }
    notice.value = result.data.message
  } catch { notice.value = 'The connection test failed before the server returned a result.' }
}

async function removeServer(server: Server) {
  if (!window.confirm(t('Delete this server and its metric history?'))) return
  try {
    await serversApi.remove(server.id)
    servers.value = servers.value.filter(item => item.id !== server.id)
    if (selectedServerId.value === server.id) selectedServerId.value = primaryServer.value?.id ?? null
    if (editingId.value === server.id) showAdd.value = false
    notice.value = 'Server deleted.'
  } catch { notice.value = 'The server could not be deleted.' }
}

function openEditor(server?: Server) {
  editingId.value = server?.id ?? null
  Object.assign(draft, {
    name: server?.name ?? '', hostname: server?.hostname ?? '', ip: server?.ip ?? '', port: server?.port ?? 22,
    username: server?.username ?? '', password: '', description: server?.description ?? '', location: server?.location ?? '',
    os: server?.os ?? '', provider: server?.provider ?? 'ssh', isPrimary: server?.isPrimary ?? false,
    capabilities: server?.capabilities.join(', ') ?? 'SSH, Monitoring',
  })
  showAdd.value = true
}

async function addServer() {
  if (saving.value) return
  if (!draft.name.trim()) { notice.value = 'Enter a server name.'; return }
  if (draft.provider === 'ssh' && ((!draft.hostname.trim() && !draft.ip.trim()) || !draft.username.trim() || (!editingId.value && !draft.password))) {
    notice.value = 'SSH servers require a host, username and password.'
    return
  }
  saving.value = true
  try {
    const payload = {
      name: draft.name.trim(), hostname: draft.hostname.trim(), ip: draft.ip.trim() || null, port: draft.port,
      username: draft.username.trim(), ...(draft.password ? { password: draft.password } : {}),
      description: draft.description.trim(), location: draft.location.trim(), os: draft.os.trim(),
      provider: draft.provider, isPrimary: draft.isPrimary,
      capabilities: draft.capabilities.split(',').map(item => item.trim()).filter(Boolean), enabled: true,
    }
    const saved = editingId.value
      ? (await serversApi.update(editingId.value, payload)).data
      : await store.createServer(payload)
    if (!saved) { notice.value = 'Server could not be saved. Check the connection fields.'; return }
    if (saved.isPrimary) for (const server of servers.value) server.isPrimary = server.id === saved.id
    const index = servers.value.findIndex(server => server.id === saved.id)
    if (index !== -1) servers.value[index] = saved
    selectedServerId.value = saved.id
    showAdd.value = false
    draft.password = ''
    notice.value = 'Host saved. Testing connection…'
    if (saved.provider === 'ssh') await testConnection(saved)
    else await refresh()
  } catch { notice.value = 'Host could not be saved. Check the address, port and credentials.' }
  finally { saving.value = false }
}

watch(intervalSeconds, startPolling)
watch(selectedServerId, () => loadMetrics())
onMounted(async () => {
  selectedServerId.value = primaryServer.value?.id ?? null
  await refresh()
  startPolling()
})
onUnmounted(stopPolling)
</script>

<template>
  <div>
    <DashboardPageHeader :title="$t('Servers')" :description="$t('Host inventory, live resource snapshots and historical utilization.')">
      <label class="refresh-interval">{{ $t("Auto refresh") }}<select v-model.number="intervalSeconds"><option :value="0">{{ $t("Off") }}</option><option :value="10">10 s</option><option :value="30">30 s</option><option :value="60">60 s</option></select></label>
      <AppButton variant="secondary" :disabled="busy" @click="refresh"><RefreshCw :size="15" /> {{ $t("Refresh now") }}</AppButton>
      <AppButton @click="openEditor()"><Plus :size="15" /> {{ $t("Add host") }}</AppButton>
    </DashboardPageHeader>
    <p v-if="notice" class="feedback" role="status">{{ $t(notice) }}</p>

    <form v-if="showAdd" class="record-editor new-server-form" @submit.prevent="addServer">
      <div class="editor-heading"><div><h2>{{ $t("Configure host connection") }}</h2><p class="muted-copy">{{ $t("Passwords are encrypted at rest and never returned by the API. The first SSH connection requires explicit host-key trust.") }}</p></div><AppButton type="submit" :disabled="saving">{{ saving ? $t('Saving…') : $t('Save host') }}</AppButton></div>
      <div class="field-grid">
        <label>{{ $t("Name") }}<input v-model="draft.name" required /></label><label>{{ $t("Connection method") }}<select v-model="draft.provider" :disabled="draft.provider === 'local'"><option v-if="draft.provider === 'local'" value="local">{{ $t("Deployment host") }}</option><option value="ssh">{{ $t("SSH / live metrics") }}</option><option value="mock">{{ $t("Mock snapshot") }}</option><option value="xui">{{ $t("3x-ui reference") }}</option></select></label>
        <label>{{ $t("Hostname") }}<input v-model="draft.hostname" :placeholder="$t('gpu8.example.com')" /></label><label>{{ $t("IP address (preferred when set)") }}<input v-model="draft.ip" placeholder="10.0.0.18" /></label>
        <label>{{ $t("Port") }}<input v-model.number="draft.port" type="number" min="1" max="65535" /></label><label>{{ $t("Username") }}<input v-model="draft.username" autocomplete="username" :placeholder="$t('ubuntu')" /></label>
        <label>{{ $t("Password") }}<input v-model="draft.password" type="password" autocomplete="new-password" :placeholder="editingId ? $t('Leave blank to keep the existing password') : $t('Stored encrypted')" /></label><label>{{ $t("Location") }}<input v-model="draft.location" /></label>
        <label>{{ $t("Operating system") }}<input v-model="draft.os" /></label><label>{{ $t("Capabilities") }}<input v-model="draft.capabilities" :placeholder="$t('SSH, Docker, Monitoring')" /></label>
      </div>
      <label>{{ $t("Description") }}<textarea v-model="draft.description" rows="2" /></label>
      <label class="check-field"><input v-model="draft.isPrimary" type="checkbox" /> {{ $t("Mark as the primary deployed host") }}</label>
      <div class="editor-actions"><AppButton type="submit" :disabled="saving">{{ saving ? $t('Saving…') : $t('Save host') }}</AppButton><button type="button" @click="showAdd = false">{{ $t("Cancel") }}</button></div>
    </form>

    <p class="muted-copy"><label><input v-model="showDemo" type="checkbox" /> {{ $t("Show demo hosts (excluded from live totals)") }}</label></p>
    <section class="fleet-summary"><div><span>{{ $t("Fleet") }}</span><strong>{{ liveServers.length }}</strong><small>{{ $t("hosts") }}</small></div><div><span>{{ $t("Availability") }}</span><strong>{{ onlineCount }} / {{ liveServers.length }}</strong><small>{{ $t("online") }}</small></div><div><span>{{ $t("GPU capacity") }}</span><strong>{{ gpuCount }}</strong><small>{{ $t("NVIDIA GPUs") }}</small></div><div><span>{{ $t("Containers") }}</span><strong>{{ containerCount }}</strong><small>{{ $t("running") }}</small></div></section>

    <section class="server-grid">
      <article v-for="server in visibleServers" :key="server.id" class="server-card" :class="{ 'is-offline': server.status === 'offline', 'is-primary': server.id === selectedServer?.id }" @click="selectedServerId = server.id">
        <header><div class="server-icon"><ServerCog :size="19" /></div><div><h2>{{ server.name }} <AppBadge v-if="server.isPrimary" tone="info">{{ $t("Primary") }}</AppBadge></h2><p>{{ server.description || $t('No host description') }}</p></div><div class="server-status"><StatusDot :status="server.status" /><span>{{ server.provider === 'mock' ? $t('Demo') : $t(server.status) }}</span></div></header>
        <div class="server-meta"><span>{{ server.os || $t('OS unknown') }}</span><span>{{ server.location || $t('Location unset') }}</span><span>{{ server.provider === 'local' ? (server.detectedHostname || $t('Awaiting host sample')) : (server.hostname || server.ip || $t('Host not set')) + ':' + (server.port || 22) }}</span><span>{{ server.metricScope === 'deployment_host' ? $t('Deployment host') : server.metricScope === 'container_runtime' ? $t('Docker runtime / VM') : server.provider || $t('mock') }}</span></div>
        <p v-if="server.lastError" class="server-connection-error" role="status">{{ $t(server.lastError) }}<span v-if="server.lastSeen"> {{ $t("Last successful sample:") }} {{ new Date(server.lastSeen).toLocaleString() }}</span></p>
        <template v-if="server.lastSeen || server.provider === 'mock'"><div class="resource-bars"><div><span>{{ $t("CPU") }} <b>{{ server.cpu }}%</b></span><i><em :style="{ width: barWidth(server.cpu) }" /></i></div><div><span>{{ $t("RAM") }} <b>{{ formatCapacity(server.memory, 3) }}</b></span><i><em :style="{ width: barWidth(server.memory.total ? server.memory.used / server.memory.total * 100 : 0) }" /></i></div><div><span>{{ $t("Disk") }} <b>{{ formatCapacity(server.disk, 4) }}</b></span><i><em :style="{ width: barWidth(server.disk.total ? server.disk.used / server.disk.total * 100 : 0) }" /></i></div></div><div v-if="server.gpus.length" class="gpu-strip"><div class="gpu-heading"><span><Cpu :size="14" /> {{ server.gpus[0].name }} × {{ server.gpus.length }}</span><small>{{ $t("GPU utilization") }}</small></div><div class="gpu-values"><span v-for="(gpu, index) in server.gpus" :key="index"><b>{{ gpu.utilization }}</b><small>%</small></span></div></div><div v-else class="no-gpu"><Cpu :size="15" /><span>{{ $t("No NVIDIA GPU reported") }}</span></div></template>
        <div v-else class="offline-state"><p>{{ server.lastError || ('Last seen ' + (server.lastSeen || $t('never')) + '.') }}</p><button type="button" @click.stop="testConnection(server)"><Wifi :size="13" /> {{ $t("Test connection") }}</button></div>
        <dl v-if="server.lastSeen" class="server-hardware"><div v-for="field in [{ key: 'cpu_model', label: 'CPU model' }, { key: 'cpu_cores', label: 'CPU cores' }, { key: 'cpu_threads', label: 'CPU threads' }, { key: 'architecture', label: 'Architecture' }, { key: 'memory_speed', label: 'Memory speed' }]" :key="field.key"><dt>{{ $t(field.label) }}</dt><dd>{{ server.hardware?.[field.key] || '—' }}</dd></div></dl>
        <footer><div class="capability-list"><AppBadge v-for="capability in server.capabilities" :key="capability">{{ capability.replace('_', ' ') }}</AppBadge></div><div class="server-card-actions"><button v-if="server.provider !== 'local'" type="button" @click.stop="openEditor(server)">{{ $t("Edit connection") }}</button><button v-if="server.provider !== 'local'" class="danger" type="button" @click.stop="removeServer(server)">{{ $t("Delete") }}</button><button type="button" @click.stop="testConnection(server)"><ShieldCheck :size="13" /> {{ $t("Test") }}</button><span><Box :size="14" /> {{ server.containersAvailable || server.provider === 'mock' ? $t(server.containers + ' running') : $t('Docker unavailable') }}</span><span>{{ $t("Uptime") }} {{ server.uptime || '—' }}</span></div></footer>
      </article>
    </section>

    <section v-if="selectedServer" class="server-history">
      <header><div><p>{{ $t("Resource history") }}</p><h2>{{ selectedServer.name }}</h2><span>{{ $t("Stored metric samples ·") }} {{ intervalSeconds ? $t('polling every ' + intervalSeconds + ' s') : $t('polling disabled') }}</span></div><button type="button" @click="loadMetrics()"><RefreshCw :size="14" /> {{ $t("Reload history") }}</button></header>
      <div v-if="metrics.length" class="metric-charts">
        <article><div><span>{{ $t("CPU") }}</span><strong>{{ metrics[metrics.length - 1].cpu.toFixed(1) }}%</strong></div><svg viewBox="0 0 480 132" preserveAspectRatio="none" role="img" :aria-label="$t('CPU usage history')"><polyline :points="chartPoints('cpu')" /></svg></article>
        <article><div><span>{{ $t("Memory") }}</span><strong>{{ metricPercent(metrics[metrics.length - 1], 'memory').toFixed(1) }}%</strong></div><svg viewBox="0 0 480 132" preserveAspectRatio="none" role="img" :aria-label="$t('Memory usage history')"><polyline :points="chartPoints('memory')" /></svg></article>
        <article><div><span>{{ $t("Disk") }}</span><strong>{{ metricPercent(metrics[metrics.length - 1], 'disk').toFixed(1) }}%</strong></div><svg viewBox="0 0 480 132" preserveAspectRatio="none" role="img" :aria-label="$t('Disk usage history')"><polyline :points="chartPoints('disk')" /></svg></article>
      </div>
      <p v-else class="empty-hint">{{ $t("No samples in the last 24 hours. Refresh the host to create the first point.") }}</p>
    </section>
  </div>
</template>
