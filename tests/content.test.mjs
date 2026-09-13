import assert from 'node:assert/strict'
import { build } from 'esbuild'
import { pathToFileURL } from 'node:url'
await build({ entryPoints: ['src/services/localizedContent.ts', 'src/services/capacity.ts'], outdir: 'node_modules/.tmp/content-tests', bundle: true, platform: 'node', format: 'esm', outExtension: { '.js': '.mjs' } })
const { resolveContent, editContent } = await import(pathToFileURL(process.cwd() + '/node_modules/.tmp/content-tests/localizedContent.mjs'))
const { formatCapacity } = await import(pathToFileURL(process.cwd() + '/node_modules/.tmp/content-tests/capacity.mjs'))
const content = { name: 'English', title: '', email: 'test@example.org', translations: { zh: { name: '中文' } }, selectedProjects: [{ title: 'Project', caption: 'Caption', mediaUrl: '/image.svg', links: [{ label: 'Paper', url: '/paper' }] }] }
const zh = editContent(content, 'zh')
assert.equal(zh.title, '')
zh.title = '研究者'
zh.selectedProjects[0].caption = '图注'
zh.selectedProjects[0].links[0].label = '论文'
assert.equal(content.selectedProjects[0].caption, 'Caption')
assert.equal(resolveContent(content, 'en').title, '研究者')
assert.equal(resolveContent(content, 'zh').selectedProjects[0].title, 'Project')
assert.equal(resolveContent(content, 'zh').selectedProjects[0].links[0].label, '论文')
assert.equal(resolveContent(content, 'zh').email, 'test@example.org')
zh.title = ' '
assert.equal(resolveContent(content, 'zh').title, '-')
assert.equal(resolveContent(content, 'en').title, '-')
const project = zh.selectedProjects[0]
Object.assign(project, { ...project, mediaUrl: '/replacement.svg' })
assert.equal(content.selectedProjects[0].caption, 'Caption')
assert.equal(content.selectedProjects[0].translations.zh.caption, '图注')
assert.equal(formatCapacity({used: .01, total: .1, usedBytes: 10*1024**3, totalBytes: 100*1024**3}, 4), '10 / 100 GiB')
assert.equal(formatCapacity({used: 512, total: 1024}, 3), '0.5 / 1 TiB')
console.log('PASS content locale fallback, independent nested edits, shared URLs, media replacement, capacity units')
