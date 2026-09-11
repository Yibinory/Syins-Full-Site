export function listData<T>(value: T[] | { results?: T[] } | null | undefined): T[] {
  if (Array.isArray(value)) return value
  return value?.results ?? []
}

export function localStorageJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) as T : fallback
  } catch {
    return fallback
  }
}

export function saveLocalStorageJson<T>(key: string, value: T) {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch { /* storage is optional */ }
}
