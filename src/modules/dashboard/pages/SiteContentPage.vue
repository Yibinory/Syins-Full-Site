<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowUpRight, Check, FileText, FlaskConical, Home, Link2, Newspaper, RotateCcw, Save, UserRound } from 'lucide-vue-next'
import MediaEditor from '@/components/shared/MediaEditor.vue'
import DashboardPageHeader from '@/components/shared/DashboardPageHeader.vue'
import AppButton from '@/components/ui/AppButton.vue'
import { useSiteContentStore, type SiteContent } from '@/stores/siteContent'

type ContentKey = Exclude<keyof SiteContent, 'selectedProjects' | 'currentResearch'>
interface ContentField { key: ContentKey; label: string; multiline?: boolean; help?: string }
interface ContentSection { id: string; label: string; description: string; icon: typeof Home; fields: ContentField[] }

const sections: ContentSection[] = [
  { id: 'identity', label: 'Profile & identity', description: 'Name, affiliation and contact details', icon: UserRound, fields: [
    { key: 'name', label: 'Display name' }, { key: 'title', label: 'Academic title' }, { key: 'location', label: 'Location' }, { key: 'email', label: 'Public email' },
  ] },
  { id: 'homepage', label: 'Homepage', description: 'Hero and introduction', icon: Home, fields: [
    { key: 'headline', label: 'Hero headline', multiline: true }, { key: 'bio', label: 'Short biography', multiline: true },
  ] },
  { id: 'research', label: 'Research', description: 'Current directions and selected projects', icon: FlaskConical, fields: [
    { key: 'researchDirections', label: 'Research directions', help: 'Separate directions with ×.' }, { key: 'currentResearchHeading', label: 'Current research heading' }, { key: 'featuredResearchHeading', label: 'Selected research heading' }, { key: 'featuredResearchIntro', label: 'Selected research introduction', multiline: true },
  ] },
  { id: 'publications', label: 'Publications', description: 'Page introduction and featured papers', icon: Newspaper, fields: [
    { key: 'publicationsHeading', label: 'Page heading' }, { key: 'publicationsDescription', label: 'Page introduction', multiline: true },
  ] },
  { id: 'notes', label: 'Notes', description: 'Library introduction; featured entries are managed in Documents', icon: FileText, fields: [
    { key: 'notesHeading', label: 'Library heading' }, { key: 'notesDescription', label: 'Library introduction', multiline: true }, 
  ] },
  { id: 'links', label: 'External links', description: 'Scholar, GitHub and curriculum vitae', icon: Link2, fields: [
    { key: 'scholarUrl', label: 'Google Scholar URL' }, { key: 'githubUrl', label: 'GitHub URL' }, { key: 'cvUrl', label: 'CV URL' },
  ] },
]

const store = useSiteContentStore()
const activeId = ref('homepage')
const justSaved = ref(false)
const activeSection = computed(() => sections.find((section) => section.id === activeId.value) ?? sections[0]!)

function addProject() {
  store.content.selectedProjects.push({ id: crypto.randomUUID(), title: 'New research project', motivation: '', approach: '', status: 'Active', mediaType: 'image', mediaUrl: '', mediaAlt: '', caption: '', links: [{ label: 'Paper', url: '' }, { label: 'Code', url: '' }] })
}

function moveProject(index: number, offset: number) {
  const projects = store.content.selectedProjects
  const target = index + offset
  if (target < 0 || target >= projects.length) return
  const [project] = projects.splice(index, 1)
  if (project) projects.splice(target, 0, project)
}

function addCurrentResearch() {
  const nextId = Math.max(0, ...store.content.currentResearch.map((item) => item.id)) + 1
  store.content.currentResearch.push({ id: nextId, number: '', title: 'New research question', text: '', status: 'Exploring', question: '', method: '', updated: 'Updated today' })
  normalizeCurrentResearchNumbers()
}

function moveCurrentResearch(index: number, offset: number) {
  const items = store.content.currentResearch
  const target = index + offset
  if (target < 0 || target >= items.length) return
  const [item] = items.splice(index, 1)
  if (item) items.splice(target, 0, item)
  normalizeCurrentResearchNumbers()
}

function removeCurrentResearch(index: number) {
  store.content.currentResearch.splice(index, 1)
  normalizeCurrentResearchNumbers()
}

function normalizeCurrentResearchNumbers() {
  store.content.currentResearch.forEach((entry, entryIndex) => { entry.number = String(entryIndex + 1).padStart(2, '0') })
}

async function saveChanges() {
  await store.save()
  justSaved.value = true
  window.setTimeout(() => { justSaved.value = false }, 1800)
}
</script>

<template>
  <div>
    <DashboardPageHeader eyebrow="Public site" :title="$t('Site content')" :description="$t('Edit the information visitors see across the public research portfolio.')">
      <RouterLink to="/" class="dashboard-preview-link">{{ $t("Preview site") }} <ArrowUpRight :size="15" /></RouterLink>
      <AppButton @click="saveChanges"><Check v-if="justSaved" :size="15" /><Save v-else :size="15" />{{ justSaved ? $t('Saved') : $t('Save changes') }}</AppButton>
    </DashboardPageHeader>

    <div class="content-manager">
      <aside class="content-section-list" :aria-label="$t('Public content sections')">
        <button v-for="section in sections" :key="section.id" type="button" :class="{ active: activeId === section.id }" @click="activeId = section.id">
          <component :is="section.icon" :size="17" />
          <span><strong>{{ $t(section.label) }}</strong><small>{{ $t(section.description) }}</small></span>
        </button>
      </aside>

      <section class="content-editor">
        <header>
          <div><p>{{ $t("Editing") }}</p><h2>{{ $t(activeSection.label) }}</h2><span>{{ $t(activeSection.description) }}</span></div>
          <button type="button" :title="$t('Restore default content')" @click="store.reset"><RotateCcw :size="15" /> {{ $t("Reset") }}</button>
        </header>
        <p v-if="activeId === 'publications'" class="manager-shortcut">{{ $t("Manage individual papers in") }} <RouterLink to="/dashboard/publications">{{ $t("Publications ↗") }}</RouterLink>.</p>
        <p v-if="activeId === 'notes'" class="manager-shortcut">{{ $t("Write notes and select homepage features in") }} <RouterLink to="/dashboard/docs">{{ $t("Documents ↗") }}</RouterLink>.</p>
        <form @submit.prevent="saveChanges">
          <label v-for="field in activeSection.fields" :key="field.key">
            <span>{{ $t(field.label) }}</span>
            <textarea v-if="field.multiline" v-model="store.content[field.key]" rows="3" />
            <input v-else v-model="store.content[field.key]" />
            <small v-if="field.help">{{ $t(field.help) }}</small>
          </label>
          <fieldset v-if="activeId === 'research'" class="project-editor-list">
            <legend>{{ $t("Selected research projects") }}</legend>
            <p>{{ $t("Upload figures, videos or interactive HTML / Vue packages. Replacing the visual keeps your project text and links.") }}</p>
            <fieldset v-for="(project, index) in store.content.selectedProjects" :key="project.id" class="project-editor">
              <legend>{{ $t("Project") }} {{ index + 1 }}</legend>
              <label><span>{{ $t("Title") }}</span><input v-model="project.title" /></label>
              <label><span>{{ $t("Status") }}</span><input v-model="project.status" /></label>
              <label><span>{{ $t("Motivation · one sentence") }}</span><textarea v-model="project.motivation" rows="2" /></label>
              <label><span>{{ $t("Approach · one sentence") }}</span><textarea v-model="project.approach" rows="2" /></label>
              <MediaEditor :model-value="project" @update:model-value="value => Object.assign(project, value)" />
              <template v-for="(link, linkIndex) in project.links" :key="linkIndex">
                <label><span>{{ $t("Link") }} {{ linkIndex + 1 }} {{ $t("label") }}</span><input v-model="link.label" /></label>
                <label><span>{{ $t("Link") }} {{ linkIndex + 1 }} {{ $t("URL") }}</span><input v-model="link.url" :placeholder="$t('https://…')" /></label>
              </template>
              <div class="project-editor-actions"><AppButton :disabled="index === 0" @click="moveProject(index, -1)">{{ $t("Move up") }}</AppButton><AppButton :disabled="index === store.content.selectedProjects.length - 1" @click="moveProject(index, 1)">{{ $t("Move down") }}</AppButton><AppButton @click="store.content.selectedProjects.splice(index, 1)">{{ $t("Remove project") }}</AppButton></div>
            </fieldset>
            <AppButton @click="addProject">{{ $t("Add project") }}</AppButton>
          </fieldset>
          <fieldset v-if="activeId === 'research'" class="project-editor-list">
            <legend>{{ $t("Current research questions") }}</legend>
            <p>{{ $t("These entries power the interactive research section on the homepage. Keep the question and current approach concise.") }}</p>
            <fieldset v-for="(item, index) in store.content.currentResearch" :key="item.id" class="project-editor">
              <legend>{{ $t("Question") }} {{ item.number }}</legend>
              <label><span>{{ $t("Title") }}</span><input v-model="item.title" /></label>
              <label><span>{{ $t("Status") }}</span><input v-model="item.status" /></label>
              <label><span>{{ $t("Summary") }}</span><textarea v-model="item.text" rows="2" /></label>
              <label><span>{{ $t("Research question") }}</span><textarea v-model="item.question" rows="2" /></label>
              <label><span>{{ $t("Current approach") }}</span><textarea v-model="item.method" rows="2" /></label>
              <label><span>{{ $t("Updated label") }}</span><input v-model="item.updated" :placeholder="$t('Updated today')" /></label>
              <div class="project-editor-actions"><AppButton :disabled="index === 0" @click="moveCurrentResearch(index, -1)">{{ $t("Move up") }}</AppButton><AppButton :disabled="index === store.content.currentResearch.length - 1" @click="moveCurrentResearch(index, 1)">{{ $t("Move down") }}</AppButton><AppButton @click="removeCurrentResearch(index)">{{ $t("Remove question") }}</AppButton></div>
            </fieldset>
            <AppButton @click="addCurrentResearch">{{ $t("Add question") }}</AppButton>
          </fieldset>
        </form>
        <footer><span><i /> {{ $t("Changes are stored in the Django workspace database.") }}</span><AppButton @click="saveChanges">{{ $t("Save changes") }}</AppButton></footer>
      </section>
    </div>
  </div>
</template>
