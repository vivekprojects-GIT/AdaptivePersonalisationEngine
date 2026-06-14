<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Button from '@/components/ui/Button.vue'
import { getAccessToken, clearAccessToken } from '@/lib/auth'
import { clearSessionUsername } from '@/lib/sessionUser'
import { getThemeMode, setThemeMode, type ThemeMode } from '@/lib/theme'
import { showToast } from '@/lib/toast'
import { ArrowRightOnRectangleIcon, TrashIcon } from '@/components/icons'

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ((typeof location !== 'undefined' && /^(localhost|127.0.0.1)$/.test(location.hostname)) ? 'http://localhost:5051' : '')

const username = ref('')
const email = ref('')
const isAdmin = ref(false)
const theme = ref<ThemeMode>(getThemeMode())
const clearing = ref(false)

const themes: { id: ThemeMode; label: string }[] = [
  { id: 'light', label: 'Light' },
  { id: 'dark', label: 'Dark' },
  { id: 'system', label: 'System' },
]

async function loadMe() {
  const token = getAccessToken()
  if (!token) return
  try {
    const r = await fetch(`${API_BASE}/api/me`, { headers: { Authorization: `Bearer ${token}` } })
    const d = await r.json().catch(() => ({}))
    if (r.ok) {
      username.value = d?.username || ''
      email.value = d?.email || ''
      isAdmin.value = Boolean(d?.is_admin)
    }
  } catch {
    /* non-fatal */
  }
}

function setTheme(t: ThemeMode) {
  theme.value = t
  setThemeMode(t)
}

async function clearChat() {
  if (clearing.value) return
  clearing.value = true
  try {
    const r = await fetch(`${API_BASE}/api/conversation/clear`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${getAccessToken()}` },
    })
    if (r.ok) showToast({ title: 'Chat history cleared', message: 'Your stored conversation was removed.' })
    else showToast({ title: 'Could not clear', message: 'Please try again.' })
  } catch {
    showToast({ title: 'Could not clear', message: 'Network error.' })
  } finally {
    clearing.value = false
  }
}

function logout() {
  clearAccessToken()
  clearSessionUsername()
  showToast({ title: 'Signed out', message: 'See you soon.' })
  router.push('/')
}

onMounted(loadMe)
</script>

<template>
  <div class="w-full px-4 lg:px-6 pb-16">
    <div class="max-w-3xl mx-auto py-8 space-y-8">
      <header>
        <h1 class="text-2xl font-semibold tracking-tight">Settings</h1>
        <p class="text-sm text-muted-foreground mt-1">Manage your account and preferences.</p>
      </header>

      <!-- Account -->
      <section class="rounded-2xl border glass-panel p-6 space-y-4">
        <h2 class="text-sm font-semibold">Account</h2>
        <div class="flex items-center gap-3">
          <span class="h-12 w-12 rounded-xl bg-primary/15 border border-primary/30 flex items-center justify-center text-lg font-semibold text-primary uppercase shrink-0">
            {{ (username || 'U').charAt(0) }}
          </span>
          <div class="min-w-0">
            <div class="text-sm font-medium truncate">
              {{ username || 'Account' }}
              <span v-if="isAdmin" class="ml-1.5 align-middle text-[10px] uppercase tracking-wide rounded px-1.5 py-0.5 bg-primary/15 text-primary">admin</span>
            </div>
            <div class="text-xs text-muted-foreground truncate">{{ email }}</div>
          </div>
        </div>
      </section>

      <!-- Appearance -->
      <section class="rounded-2xl border glass-panel p-6 space-y-4">
        <h2 class="text-sm font-semibold">Appearance</h2>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="t in themes"
            :key="t.id"
            type="button"
            class="rounded-lg border px-4 py-2 text-sm transition cursor-pointer"
            :class="theme === t.id ? 'border-primary/40 bg-primary/10 text-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'"
            @click="setTheme(t.id)"
          >
            {{ t.label }}
          </button>
        </div>
      </section>

      <!-- Data -->
      <section class="rounded-2xl border glass-panel p-6 space-y-3">
        <h2 class="text-sm font-semibold">Your data</h2>
        <p class="text-sm text-muted-foreground max-w-xl">
          Your chat history and the format preferences learned from it are private to your account.
          Clearing removes the stored conversation for this account.
        </p>
        <Button variant="outline" class="h-9 gap-2 text-destructive border-destructive/30 hover:bg-destructive/10" :disabled="clearing" @click="clearChat">
          <TrashIcon class="h-4 w-4" />
          {{ clearing ? 'Clearing…' : 'Clear my chat history' }}
        </Button>
      </section>

      <!-- Sign out -->
      <div class="pt-2">
        <Button variant="outline" class="h-10 gap-2" @click="logout">
          <ArrowRightOnRectangleIcon class="h-4 w-4" />
          Sign out
        </Button>
      </div>
    </div>
  </div>
</template>
