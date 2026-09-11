import { unzipSync, strFromU8 } from 'fflate'
import * as esbuild from 'esbuild-wasm'
import wasmURL from 'esbuild-wasm/esbuild.wasm?url'
import { parse, compileScript, compileTemplate, compileStyle } from '@vue/compiler-sfc/dist/compiler-sfc.esm-browser.js'
import vueRuntime from 'vue/dist/vue.esm-browser.prod.js?raw'

let initialized: Promise<void> | undefined
const MAX_BYTES = 40 * 1024 * 1024
const decode = (v: Uint8Array) => strFromU8(v)
function normalize(path: string) {
  const parts: string[] = []
  for (const part of path.replaceAll('\\', '/').split('/')) { if (!part || part === '.') continue; if (part === '..') { if (!parts.length) throw new Error('A file path leaves the archive.'); parts.pop() } else parts.push(part) }
  return parts.join('/')
}
function dataURL(bytes: Uint8Array, mime: string) { let s = ''; for (let i = 0; i < bytes.length; i += 8192) s += String.fromCharCode(...bytes.subarray(i, i + 8192)); return `data:${mime};base64,${btoa(s)}` }
const mimeFor = (path: string) => ({ svg: 'image/svg+xml', png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', webp: 'image/webp', gif: 'image/gif', woff2: 'font/woff2', woff: 'font/woff', mp4: 'video/mp4', webm: 'video/webm' }[path.split('.').pop() || ''] || 'application/octet-stream')
const escapeScript = (text: string) => text.replace(/<\/script/gi, '<\\/script')
export const interactivePolicy = "default-src 'none'; script-src 'unsafe-inline' blob:; style-src 'unsafe-inline'; img-src data: blob:; media-src data: blob:; font-src data:; connect-src 'none'; base-uri 'none'; form-action 'none';"
export function isolateHTML(html: string) { return `<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="${interactivePolicy}"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>${html}</body></html>` }

export async function compileInteractive(file: File): Promise<string> {
  const bytes = new Uint8Array(await file.arrayBuffer())
  let files: Record<string, Uint8Array> = {}
  if (file.name.toLowerCase().endsWith('.zip')) {
    let total = 0; let count = 0
    files = unzipSync(bytes, { filter(info) { total += info.originalSize; count++; if (total > MAX_BYTES || count > 300) throw new Error('Archive is too large: use at most 300 files and 40 MB unpacked.'); if (info.name.startsWith('/') || info.name.includes('\\') || info.name.split('/').includes('..')) throw new Error('Unsafe archive path.'); return !info.name.endsWith('/') && !info.name.includes('__MACOSX/') } })
  } else files[normalize(file.name)] = bytes
  const names = Object.keys(files)
  const htmlEntries = names.filter(p => /(^|\/)index\.html?$/i.test(p))
  const vueEntries = names.filter(p => /(^|\/)App\.vue$/.test(p))
  const entry = file.name.toLowerCase().endsWith('.zip') ? (htmlEntries.length === 1 ? htmlEntries[0] : !htmlEntries.length && vueEntries.length === 1 ? vueEntries[0] : undefined) : names[0]
  if (!entry) throw new Error('ZIP must contain one index.html or one App.vue entry. Upload a built dist folder for projects with other dependencies.')
  const root = entry.includes('/') ? entry.slice(0, entry.lastIndexOf('/') + 1) : ''
  function resolvePath(path: string, importer: string) {
    if (/^(https?:|\/\/)/i.test(path)) throw new Error('External resources are not bundled. Include scripts, styles and media in the ZIP.')
    const clean = path.split(/[?#]/)[0]!
    const base = clean.startsWith('/') ? root + clean.slice(1) : (importer.includes('/') ? importer.slice(0, importer.lastIndexOf('/') + 1) : '') + clean
    const result = normalize(base)
    const found = [result, result + '.ts', result + '.js', result + '.vue', result + '/index.ts', result + '/index.js'].find(p => files[p])
    if (!found) throw new Error(`Missing archive resource: ${path}`)
    return found
  }
  function rewriteCSS(css: string, from: string): string {
    if (/@import\s/i.test(css)) throw new Error('Please bundle CSS @import rules before uploading.')
    return css.replace(/url\(\s*(['"]?)(.*?)\1\s*\)/g, (_, _quote, url: string) => {
      if (/^(data:|#)/.test(url)) return `url("${url}")`
      const path = resolvePath(url, from); return `url("${dataURL(files[path]!, mimeFor(path))}")`
    })
  }
  const styles = new Map<string, string>()
  const plugin: esbuild.Plugin = {
    name: 'archive', setup(build) {
      build.onResolve({ filter: /.*/ }, args => {
        if (args.path === 'vue') return { path: 'vue', namespace: 'archive' }
        if (args.path === '__entry__') return { path: '__entry__', namespace: 'archive' }
        if (!args.path.startsWith('.') && !args.path.startsWith('/') && args.importer !== '__entry__') throw new Error(`Dependency ${args.path} is not included. Supported: Vue and local files. Otherwise upload a built HTML package.`)
        return { path: resolvePath(args.path, args.importer === '__entry__' ? entry! : args.importer), namespace: 'archive' }
      })
      build.onLoad({ filter: /.*/, namespace: 'archive' }, async args => {
        if (args.path === 'vue') return { contents: vueRuntime, loader: 'js' }
        if (args.path === '__entry__') return { contents: decode(files.__entry__!), loader: 'js' }
        const ext = args.path.split('.').pop()!
        if (ext === 'vue') {
          const { descriptor: d, errors } = parse(decode(files[args.path]!), { filename: args.path })
          if (errors.length) throw new Error(String(errors[0]))
          if ([d.script, d.scriptSetup, d.template, ...d.styles].some(b => b?.src)) throw new Error('Vue external src blocks are not supported; use local component imports.')
          if (d.styles.some(s => s.lang || s.module)) throw new Error('Use plain CSS in Vue components, or upload a built HTML package.')
          if (d.template?.lang) throw new Error('Use a standard HTML template.')
          const id = 'asset-' + args.path.replace(/\W/g, '-')
          let code = ''
          if (d.script || d.scriptSetup) code = compileScript(d, { id, genDefaultAs: '__sfc__', inlineTemplate: false }).content
          else code = 'const __sfc__ = {};'
          if (d.template) { const template = compileTemplate({ source: d.template.content, filename: args.path, id, scoped: d.styles.some(s => s.scoped), transformAssetUrls: true, compilerOptions: { bindingMetadata: d.script || d.scriptSetup ? compileScript(d, { id }).bindings : {} } }); if (template.errors.length) throw new Error(String(template.errors[0])); code += '\n' + template.code + '\n__sfc__.render = render;' }
          if (d.styles.some(s => s.scoped)) code += `\n__sfc__.__scopeId = ${JSON.stringify('data-v-' + id)};`
          for (const [i, style] of d.styles.entries()) { const css = compileStyle({ source: style.content, filename: args.path, id: 'data-v-' + id, scoped: style.scoped }); if (css.errors.length) throw new Error(String(css.errors[0])); styles.set(`${args.path}:${i}`, rewriteCSS(css.code, args.path)) }
          return { contents: code + '\nexport default __sfc__;', loader: 'ts' }
        }
        if (ext === 'css') { styles.set(args.path, rewriteCSS(decode(files[args.path]!), args.path)); return { contents: '', loader: 'js' } }
        if (['js', 'mjs', 'ts', 'json'].includes(ext)) return { contents: decode(files[args.path]!), loader: ext === 'mjs' ? 'js' : ext as esbuild.Loader }
        return { contents: `export default ${JSON.stringify(dataURL(files[args.path]!, mimeFor(args.path)))};`, loader: 'js' }
      })
    },
  }
  async function bundle(source: string) {
    initialized ??= esbuild.initialize({ wasmURL, worker: true })
    await initialized
    files.__entry__ = new TextEncoder().encode(source)
    const result = await esbuild.build({ entryPoints: ['__entry__'], bundle: true, write: false, logLevel: 'silent', plugins: [plugin], format: 'iife', platform: 'browser', target: 'es2022', define: { 'process.env.NODE_ENV': '"production"', __VUE_OPTIONS_API__: 'true', __VUE_PROD_DEVTOOLS__: 'false' } })
    return result.outputFiles[0]!.text
  }
  let body = ''
  if (entry.toLowerCase().endsWith('.vue')) {
    const code = await bundle(`import { createApp } from 'vue'; import App from './${entry.split('/').pop()}'; createApp(App).mount('#app');`)
    body = `<div id="app"></div><script>${escapeScript(code)}</script>`
  } else {
    const doc = new DOMParser().parseFromString(decode(files[entry]!), 'text/html')
    doc.querySelectorAll('base, meta[http-equiv], iframe, object, embed').forEach(e => e.remove())
    for (const link of doc.querySelectorAll('link')) {
      if (link.getAttribute('rel') === 'stylesheet') { const path = resolvePath(link.getAttribute('href') || '', entry); const style = doc.createElement('style'); style.textContent = rewriteCSS(decode(files[path]!), path); link.replaceWith(style) } else link.remove()
    }
    for (const style of doc.querySelectorAll('style')) style.textContent = rewriteCSS(style.textContent || '', entry)
    for (const element of doc.querySelectorAll('[style]')) element.setAttribute('style', rewriteCSS(element.getAttribute('style') || '', entry))
    for (const element of doc.querySelectorAll('img, source, video, audio, image')) {
      for (const attr of ['src', 'poster', 'href', 'xlink:href']) { const src = element.getAttribute(attr); if (src && !src.startsWith('data:') && !src.startsWith('#')) { const path = resolvePath(src, entry); element.setAttribute(attr, dataURL(files[path]!, mimeFor(path))) } }
      if (element.hasAttribute('srcset')) throw new Error('Use src instead of srcset in interactive packages.')
    }
    const deferredScripts: string[] = []
    for (const script of doc.querySelectorAll('script')) {
      const type = script.getAttribute('type')
      if (type && !['module', 'text/javascript', 'application/javascript'].includes(type)) { if (type === 'importmap') throw new Error('Import maps are not supported. Bundle dependencies before uploading.'); continue }
      let source = script.textContent || ''; const src = script.getAttribute('src')
      if (src) { const path = resolvePath(src, entry); if (type === 'module') source = `import './${path.startsWith(root) ? path.slice(root.length) : path}';`; else source = decode(files[path]!) }
      if (type === 'module') source = await bundle(source)
      if (type === 'module' || script.hasAttribute('defer')) { deferredScripts.push(`<script>${escapeScript(source)}</script>`); script.remove(); continue }
      script.removeAttribute('src'); script.removeAttribute('type'); script.removeAttribute('integrity'); script.textContent = escapeScript(source)
    }
    body = doc.head.innerHTML + doc.body.innerHTML + deferredScripts.join('')
  }
  const css = [...styles.values()].join('\n').replace(/<\/style/gi, '<\\/style')
  return isolateHTML(`<style>html,body{margin:0;min-height:100%;font-family:system-ui,sans-serif}*{box-sizing:border-box}${css}</style>${body}`)
}
