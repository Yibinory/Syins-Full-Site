import { defineStore } from 'pinia'
import { ref } from 'vue'
import { http } from '@/services/http'

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(false)
  const user = ref<{ id: number; username: string; email: string; isStaff: boolean; displayName: string } | null>(null)
  const ready = ref(false)

  function applySession(payload: { authenticated: boolean; user: typeof user.value }) {
    isAuthenticated.value = payload.authenticated
    user.value = payload.user
    if (payload.authenticated) localStorage.setItem('research-os:backend-auth', 'true')
    else localStorage.removeItem('research-os:backend-auth')
  }

  async function hydrate() {
    if (ready.value) return
    try {
      const response = await http.get<{ authenticated: boolean; user: typeof user.value }>('/auth/session/')
      applySession(response.data)
    } catch {
      applySession({ authenticated: false, user: null })
    } finally {
      ready.value = true
    }
  }

  async function login(email: string, password: string) {
    if (!email.trim() || !password.trim()) return false
    try {
      const response = await http.post<{ authenticated: boolean; user: typeof user.value }>('/auth/login/', { email, password })
      applySession(response.data)
      return true
    } catch {
      applySession({ authenticated: false, user: null })
      return false
    }
  }

  async function logout() {
    try { await http.post('/auth/logout/') } catch { /* the local session is still cleared */ }
    applySession({ authenticated: false, user: null })
  }

  return { isAuthenticated, user, ready, hydrate, login, logout }
})
