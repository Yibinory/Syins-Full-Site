import assert from 'node:assert/strict'
import { build } from 'esbuild'
import { pathToFileURL } from 'node:url'
import { createPinia, setActivePinia, disposePinia } from 'pinia'
import { nextTick } from 'vue'
import { parseHTML } from 'linkedom'
globalThis.Storage = class Storage {}
const values = new Map()
globalThis.localStorage = { getItem: key => values.get(key) ?? null, setItem: (key,value) => values.set(key, value), removeItem: key => values.delete(key) }
const dom = parseHTML('<html><body></body></html>')
globalThis.window = dom.window; globalThis.document = dom.document
window.localStorage = globalThis.localStorage
globalThis.CustomEvent = window.CustomEvent
await build({ entryPoints: ['src/stores/workspace.ts'], outfile: 'node_modules/.tmp/research-tests/workspace.mjs', bundle: true, platform: 'node', format: 'esm', packages: 'external', alias: { '@': process.cwd() + '/src' } })
const { useWorkspaceStore, newId, today } = await import(pathToFileURL(process.cwd() + '/node_modules/.tmp/research-tests/workspace.mjs'))
let pinia = createPinia(); setActivePinia(pinia)
const store = useWorkspaceStore()
const first = store.papers[0]; const second = store.papers[1]
assert.equal(first.noteIds.length, 0)
store.linkNote(first.id, store.documents[0].id, true)
store.linkNote(first.id, store.documents[1].id, true)
store.linkNote(first.id, store.documents[0].id, true)
assert.equal(first.noteIds.length, 2, 'Paper can link multiple notes without duplicate links')
store.linkNote(second.id, store.documents[0].id, true)
assert.equal(second.noteIds.length, 1, 'One note can be linked from multiple papers')
const noteID = store.documents[0].id
const doc = JSON.parse(JSON.stringify(store.documents[0])); doc.title = 'Renamed linked note'; store.saveDocument(doc)
assert.equal(store.documents.find(n => n.id === first.noteIds[0]).title, 'Renamed linked note')
store.trashDocument(noteID)
assert.ok(first.noteIds.includes(noteID), 'Trashing a document retains existing links for restoration')
store.linkNote(first.id, noteID, false)
assert.equal(first.noteIds.length, 1)
assert.ok(store.documents.some(d => d.id === noteID), 'Unlinking does not delete the note')
store.linkNote(first.id, noteID, true)
assert.equal(first.noteIds.length, 1, 'Cannot newly link a trashed note')
const restored = JSON.parse(JSON.stringify(store.documents.find(n=>n.id===noteID))); restored.trashedAt = null; store.saveDocument(restored)
store.linkNote(first.id, noteID, true)
assert.equal(first.noteIds.length, 2)
first.tags = ['Custom', 'MRI']; store.documents[0].tags = ['custom']; store.publications[0].tags = ['CUSTOM', 'MRI']
store.renameTag('Custom', 'MRI')
assert.deepEqual([...first.tags], ['MRI']); assert.deepEqual([...store.publications[0].tags], ['MRI']); assert.deepEqual([...store.documents[0].tags], ['MRI'])
store.renameTag('MRI', '')
assert.equal(first.tags.length, 0)
store.settings.defaultNoteVisibility = 'private'
const id = newId(); store.saveDocument({ ...doc, id, title: 'Private draft', slug: `note-${id}`, visibility: store.settings.defaultNoteVisibility, publishedAt: today(), trashedAt: null })
assert.equal(store.documents.find(d=>d.id===id).visibility, 'private')
await nextTick(); await new Promise(r=>setTimeout(r,20))
assert.ok(values.has('research-os:papers'), 'Paper changes are persisted')
assert.ok(values.has('research-os:documents'), 'Document changes are persisted')
disposePinia(pinia); pinia = createPinia(); setActivePinia(pinia)
const reloaded = useWorkspaceStore()
assert.equal(reloaded.papers[0].noteIds.length, 2)
assert.equal(reloaded.documents.find(d=>d.id===id).visibility, 'private')
assert.equal(reloaded.documents.find(d=>d.id===noteID).title, 'Renamed linked note')
console.log('PASS many-to-many note links, renaming, unlinking, Trash/restore, tag merging, private defaults and persistence')
disposePinia(pinia)
