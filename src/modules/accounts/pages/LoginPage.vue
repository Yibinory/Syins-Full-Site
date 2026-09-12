<script setup lang="ts">
import LanguageSwitch from '@/components/shared/LanguageSwitch.vue'
import { ArrowLeft, ArrowRight, LockKeyhole } from 'lucide-vue-next'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppButton from '@/components/ui/AppButton.vue'
import { useAuthStore } from '@/stores/auth'

const email = ref('')
const password = ref('')
const error = ref('')
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

async function submit() {
  error.value = ''
  if (!await auth.login(email.value, password.value)) { error.value = 'Invalid email or password.'; return }
  router.push(typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard')
}
</script>

<template>
  <main class="login-page"><div class="login-language"><LanguageSwitch /></div>
    <RouterLink to="/" class="login-back"><ArrowLeft :size="16" /> {{ $t("Public site") }}</RouterLink>
    <section class="login-panel">
      <div class="login-mark"><LockKeyhole :size="19" /></div>
      <p class="login-kicker">{{ $t("Private workspace") }}</p>
      <h1>{{ $t("Research OS") }}</h1>
      <p class="login-copy">{{ $t("Your literature, research, servers, and working documents in one quiet place.") }}</p>
      <form @submit.prevent="submit">
        <label>{{ $t("Email") }}<input v-model="email" type="email" autocomplete="username" :placeholder="$t('Administrator email')" /></label>
        <label>{{ $t("Password") }}<input v-model="password" type="password" autocomplete="current-password" :placeholder="$t('Password')" /></label>
        <p v-if="error" class="form-error">{{ $t(error) }}</p>
        <AppButton type="submit">{{ $t("Enter workspace") }} <ArrowRight :size="16" /></AppButton>
      </form>
      <p class="demo-note">{{ $t("Sign in with the administrator account configured during deployment.") }}</p>
    </section>
  </main>
</template>
