import { ref, watch } from 'vue'
import zh from './zh'
export type Locale = 'en' | 'zh'
function initialLocale(): Locale { try { return localStorage.getItem('research-os:locale') === 'zh' ? 'zh' : 'en' } catch { return 'en' } }
export const locale = ref<Locale>(initialLocale())
export function t(value: unknown): string {
  const key = String(value ?? '')
  if (locale.value !== 'zh') return key
  if (zh[key]) return zh[key]
  const patterns: [RegExp, (match: RegExpMatchArray) => string][] = [
    [/^Testing connection to (.+)…$/, m => `正在测试 ${m[1]} 的连接…`],
    [/^(\d+) host\(s\) could not be refreshed\. See the connection details below\.$/, m => `${m[1]} 台主机刷新失败，请查看下方连接详情。`],
    [/^polling every (\d+) s$/, m => `每 ${m[1]} 秒刷新`],
    [/^(\d+) running$/, m => `${m[1]} 个运行中`],
    [/^Last seen (.+)$/, m => `上次在线：${m[1]}`],
    [/^Host key confirmation required before connecting \((.+)\)$/, m => `连接前请确认主机指纹（${m[1]}）`],
    [/^SSH connection failed: (.+)$/, m => `SSH 连接失败：${m[1]}`],
    [/^SSH handshake failed: (.+)$/, m => `SSH 握手失败：${m[1]}`],
  ]
  for (const [pattern, translate] of patterns) { const match = key.match(pattern); if (match) return translate(match) }
  return key
}
export function setLocale(value: Locale) { locale.value = value }
watch(locale, value => {
  document.documentElement.lang = value === 'zh' ? 'zh-CN' : 'en'
  try { localStorage.setItem('research-os:locale', value) } catch { /* Optional persistence. */ }
}, { immediate: true })
declare module 'vue' { interface ComponentCustomProperties { $t: typeof t } }
