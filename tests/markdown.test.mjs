import assert from 'node:assert/strict'
import { build } from 'esbuild'
import { JSDOM } from 'jsdom'
import { pathToFileURL } from 'node:url'
const dom = new JSDOM('<!doctype html><html><body></body></html>')
globalThis.window = dom.window
globalThis.document = dom.window.document
await build({ entryPoints: ['src/services/markdown.ts'], outfile: 'node_modules/.tmp/research-tests/markdown.mjs', bundle: true, platform: 'node', format: 'esm', packages: 'external' })
const { renderMarkdown } = await import(pathToFileURL(process.cwd() + '/node_modules/.tmp/research-tests/markdown.mjs'))
function parse(text) { return new JSDOM(renderMarkdown(text)).window.document }
for (const source of [String.raw`Inline $V_i$ end`, String.raw`Inline \(V_i\) end`, '$$\nV_i = \\frac{a}{b}\n$$', '\\[\n\\sum_{i=1}^n V_i\n\\]', '> $V_i$', '- $V_i$', '| x |\n|---|\n| $V_i$ |']) {
  const doc = parse(source)
  assert.equal(doc.querySelectorAll('.katex').length, 1, source)
  assert.ok(doc.querySelector('math'), 'Accessible MathML retained')
  assert.ok(doc.querySelector('[style]'), 'KaTeX layout styles retained')
}
let doc = parse('`$V_i$`\n\n```tex\n\\(V_i\\)\n```\n\nV\\_i\n\nCost $5 and $10. Escaped \\$x\\$.')
assert.equal(doc.querySelectorAll('.katex').length, 0)
assert.match(doc.body.textContent, /V_i/)
doc = parse('<script>alert(1)</script><img src=x onerror="alert(1)"><span style="position:fixed">text</span> $\\href{javascript:alert(1)}{X}$')
assert.equal(doc.querySelector('script,[onerror],a[href^="javascript:"]'), null)
assert.equal(doc.querySelector('span[style="position:fixed"]'), null)
assert.doesNotThrow(() => renderMarkdown('$\\unknownCommand{V}$'))
assert.ok(parse('$$\na^2+b^2=c^2\n$$').querySelector('.katex-display'))
console.log('PASS Markdown math delimiters, code/escape preservation, malformed formulas and sanitization')
