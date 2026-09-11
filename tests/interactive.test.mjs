import assert from 'node:assert/strict'
import { readFile, mkdir, writeFile } from 'node:fs/promises'
import { build } from 'esbuild'
import { pathToFileURL } from 'node:url'
import { DOMParser, parseHTML } from 'linkedom'
import { zipSync, strToU8 } from 'fflate'
import { indexedDB } from 'fake-indexeddb'
import vm from 'node:vm'

const root = process.cwd()
await mkdir('node_modules/.tmp/research-tests', { recursive: true })
await build({ entryPoints: ['src/services/interactiveCompiler.ts'], outfile: 'node_modules/.tmp/research-tests/compiler.mjs', bundle: true, platform: 'node', format: 'esm', packages: 'external', plugins: [{ name: 'test-adapters', setup(b) {
  b.onResolve({ filter: /^esbuild-wasm$/ }, () => ({ path: root + '/tests/esbuild-adapter.mjs' }))
  b.onResolve({ filter: /\.wasm\?url$/ }, () => ({ path: 'wasm', namespace: 'empty' }))
  b.onLoad({ filter: /.*/, namespace: 'empty' }, () => ({ contents: 'export default ""', loader: 'js' }))
  b.onResolve({ filter: /\?raw$/ }, a => ({ path: root + '/node_modules/' + a.path.slice(0,-4), namespace: 'raw' }))
  b.onLoad({ filter: /.*/, namespace: 'raw' }, async a => ({ contents: await readFile(a.path, 'utf8'), loader: 'text' }))
} }] })
await build({ entryPoints: ['src/services/mediaLibrary.ts'], outfile: 'node_modules/.tmp/research-tests/media.mjs', bundle: true, platform: 'node', format: 'esm', packages: 'external', plugins: [{ name: 'compiler', setup(b) { b.onResolve({ filter: /\.\/interactiveCompiler$/ }, () => ({ path: './compiler.mjs', external: true })) } }] })
globalThis.DOMParser = DOMParser
globalThis.indexedDB = indexedDB
const { compileInteractive } = await import(pathToFileURL(root + '/node_modules/.tmp/research-tests/compiler.mjs'))
const { importMedia, getMedia, deleteMedia } = await import(pathToFileURL(root + '/node_modules/.tmp/research-tests/media.mjs'))
const file = (name, text) => new File([text], name)
const zipped = (files) => new File([zipSync(Object.fromEntries(Object.entries(files).map(([p,t]) => [p,strToU8(t)])))], 'example.zip')
let passed = 0
async function check(name, fn) { await fn(); passed++; console.log(`PASS ${name}`) }
await check('HTML imports as an isolated self-contained document', async () => {
  const html = await compileInteractive(file('demo.html', '<html><head></head><body><button onclick="this.textContent=\'done\'">Try</button></body></html>'))
  assert.match(html, /Content-Security-Policy/); assert.match(html, /connect-src 'none'/); assert.match(html, /<button/)
})
await check('ZIP resolves nested local CSS, media and deferred module script', async () => {
  const html = await compileInteractive(zipped({ 'dist/index.html': '<html><head><link rel="stylesheet" href="./assets/style.css"><script type="module" src="./assets/main.js"></script></head><body><div id="output"></div><img src="./assets/a.svg"></body></html>', 'dist/assets/style.css': 'body { background: url(./a.svg) }', 'dist/assets/a.svg': '<svg xmlns="http://www.w3.org/2000/svg"/>', 'dist/assets/main.js': "document.querySelector('#output').textContent='Ready'" }))
  assert.match(html, /data:image\/svg\+xml;base64/); assert.ok(html.indexOf('id="output"') < html.lastIndexOf('<script>')); assert.doesNotMatch(html, /src="\.\/assets/)
})
await check('Vue script setup and TypeScript compile and execute a reactive interaction', async () => {
  const source = `<script setup lang="ts">import { ref } from 'vue'; const count = ref<number>(0)</script><template><button @click="count++">Count {{ count }}</button></template><style scoped>button { color: red }</style>`
  const html = await compileInteractive(file('Counter.vue', source)); assert.match(html, /data-v-asset-Counter-vue/)
  const { window, document } = parseHTML('<html><body><div id="app"></div></body></html>')
  const context = { window, document, console, Element: window.Element, SVGElement: window.SVGElement, MathMLElement: window.HTMLElement, HTMLElement: window.HTMLElement, Event: window.Event, setTimeout, clearTimeout }
  const code = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n')
  vm.runInNewContext(code, context)
  assert.equal(document.querySelector('button').textContent, 'Count 0')
  document.querySelector('button').dispatchEvent(new window.Event('click')); await Promise.resolve(); await Promise.resolve()
  assert.equal(document.querySelector('button').textContent, 'Count 1')
})
await check('Vue ZIP supports local components and image imports', async () => {
  const html = await compileInteractive(zipped({ 'demo/App.vue': `<script setup>import Child from './Child.vue'</script><template><Child /><img src="./figure.svg" /></template>`, 'demo/Child.vue': '<template><p>Child component</p></template>', 'demo/figure.svg': '<svg xmlns="http://www.w3.org/2000/svg" />' }))
  assert.match(html, /Child component/); assert.match(html, /data:image\/svg\+xml;base64/)
})
await check('Archive traversal and missing dependencies fail clearly', async () => {
  await assert.rejects(() => compileInteractive(zipped({ '../index.html': '<html></html>' })), /Unsafe archive path/)
  await assert.rejects(() => compileInteractive(zipped({ 'index.html': '<html><body><img src="missing.png"></body></html>' })), /Missing archive resource/)
  await assert.rejects(() => compileInteractive(file('Demo.vue', `<script setup>import x from 'uninstalled-library'</script><template>{{x}}</template>`)), /not included/)
})
await check('Remote resources and oversized archives are rejected', async () => {
  await assert.rejects(() => compileInteractive(file('demo.html', '<html><body><script src="https://example.com/script.js"></script></body></html>')), /External resources/)
  await assert.rejects(() => compileInteractive(zipped(Object.fromEntries(Array.from({length:301}, (_,i)=>[`${i}.txt`,'a'])))), /too large/)
})
await check('Imported files persist and clearing removes the stored file', async () => {
  const a = await importMedia(file('demo.html','<html><body>Example</body></html>'))
  const restored = await getMedia(a.id); assert.equal(restored.name, 'demo.html'); assert.match(await restored.rendered.text(), /Example/)
  await assert.rejects(() => importMedia(file('unsupported.exe', 'x')), /Choose an image/)
  assert.ok(await getMedia(a.id), 'Failed replacement preserves earlier asset')
  await deleteMedia(a.id); assert.equal(await getMedia(a.id), undefined)
})
console.log(`${passed} interactive import checks passed.`)
