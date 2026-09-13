type Language = 'en' | 'zh'
const textFields = new Set(['name', 'title', 'location', 'headline', 'bio', 'researchDirections', 'featuredResearchIntro', 'currentResearchHeading', 'featuredResearchHeading', 'publicationsHeading', 'publicationsDescription', 'notesHeading', 'notesDescription', 'papersHeading', 'papersDescription', 'toolsHeading', 'toolsDescription', 'motivation', 'approach', 'status', 'mediaAlt', 'caption', 'label', 'text', 'question', 'method', 'updated'])
type RecordValue = Record<string, any>

// Legacy text remains the English value, so existing clients and saved content stay compatible.
export function resolveContent<T>(value: T, language: Language): T {
  if (Array.isArray(value)) return value.map(item => resolveContent(item, language)) as T
  if (!value || typeof value !== 'object') return value
  const record = value as RecordValue
  return Object.fromEntries(Object.entries(record).map(([key, item]) => {
    if (textFields.has(key)) {
      const english = typeof item === 'string' ? item.trim() : ''
      const chinese = typeof record.translations?.zh?.[key] === 'string' ? record.translations.zh[key].trim() : ''
      return [key, (language === 'zh' ? chinese || english : english || chinese) || '-']
    }
    return [key, key === 'translations' ? item : resolveContent(item, language)]
  })) as T
}

// The editor never shows fallback text as an entered translation.
export function editContent<T extends object>(value: T, language: Language): T {
  const cache = new WeakMap<object, object>()
  function wrap(object: RecordValue): any {
    if (cache.has(object)) return cache.get(object)
    const proxy = new Proxy(object, {
      get(target, key, receiver) {
        if (typeof key === 'string' && textFields.has(key) && language === 'zh') return target.translations?.zh?.[key] ?? ''
        const result = Reflect.get(target, key, receiver)
        return key !== 'translations' && result && typeof result === 'object' ? wrap(result) : result
      },
      set(target, key, next) {
        if (typeof key === 'string' && textFields.has(key) && language === 'zh') {
          target.translations ??= {}
          target.translations.zh ??= {}
          target.translations.zh[key] = next
          return true
        }
        return Reflect.set(target, key, next)
      },
    })
    cache.set(object, proxy)
    return proxy
  }
  return wrap(value)
}
