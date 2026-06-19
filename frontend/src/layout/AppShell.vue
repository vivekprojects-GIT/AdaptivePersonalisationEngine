<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import FormatField from '@/components/viz/FormatField.vue'
import { clearAccessToken, getAccessToken } from '@/lib/auth'
import { clearSessionUsername, setSessionUsername } from '@/lib/sessionUser'
import { getThemeMode, setThemeMode, type ThemeMode } from '@/lib/theme'
import { showToast } from '@/lib/toast'
import {
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  ChatBubbleLeftRightIcon,
  HomeIcon,
  InformationCircleIcon,
  SparklesIcon,
} from '@/components/icons'
import AccountMenu from '@/components/AccountMenu.vue'

const route = useRoute()
const router = useRouter()
const showMobileNav = ref(false)

const theme = ref<ThemeMode>(getThemeMode())
const themeLabel = computed(() => (theme.value === 'system' ? 'System' : theme.value === 'dark' ? 'Dark' : 'Light'))

const API_BASE = import.meta.env.VITE_API_BASE_URL || ((typeof location !== 'undefined' && /^(localhost|127.0.0.1)$/.test(location.hostname)) ? 'http://localhost:5051' : '')
const isAdmin = ref(false)
const username = ref('')

const isChatRoute = computed(() => route.path.startsWith('/app/chat'))

const navItems = [
  { to: '/', label: 'Home', icon: HomeIcon, exact: true },
  { to: '/app/chat', label: 'Chat', icon: ChatBubbleLeftRightIcon },
  { to: '/app/about', label: 'About', icon: InformationCircleIcon },
]

function isActive(to: string, exact = false) {
  return exact ? route.path === to : route.path === to || route.path.startsWith(to + '/')
}
function navClass(to: string, exact = false) {
  return [
    'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[13px] font-medium transition-colors',
    isActive(to, exact)
      ? 'bg-muted/70 text-foreground'
      : 'text-muted-foreground hover:text-foreground hover:bg-muted/40',
  ]
}

async function loadMe() {
  const token = getAccessToken()
  if (!token) return
  try {
    const r = await fetch(`${API_BASE}/api/me`, { headers: { Authorization: `Bearer ${token}` } })
    const d = await r.json().catch(() => ({}))
    if (r.ok) {
      isAdmin.value = Boolean(d?.is_admin)
      username.value = d?.username || ''
      setSessionUsername(d?.username)
    }
  } catch {
    /* non-fatal */
  }
}

function logout() {
  clearAccessToken()
  clearSessionUsername()
  showToast({ title: 'Signed out', message: 'See you soon.' })
  router.push('/login')
}

function cycleTheme() {
  theme.value = theme.value === 'system' ? 'light' : theme.value === 'light' ? 'dark' : 'system'
  setThemeMode(theme.value)
}

onMounted(async () => {
  await loadMe()
})
</script>

<template>
  <div class="min-h-screen flex flex-col text-foreground relative">
    <!-- subtle format-field backdrop — APE's core idea: many answer formats, one chosen -->
    <div class="fixed inset-0 z-0 opacity-70 pointer-events-none" aria-hidden="true"><FormatField /></div>
    <!-- ===================== TOP NAV ===================== -->
    <header class="sticky top-0 z-50 glass-panel border-b/70">
      <div class="max-w-7xl mx-auto px-4 lg:px-6 h-[52px] flex items-center justify-between gap-4">
        <!-- brand -->
        <RouterLink to="/" class="flex items-center gap-2.5 min-w-0">
          <svg viewBox="0 0 100 100" class="h-7 w-7" aria-hidden="true">
            <rect x="2" y="2" width="96" height="96" rx="27" fill="#131316" />
            <rect x="26" y="31" width="48" height="9" rx="4" fill="#ffffff" />
            <rect x="26" y="46" width="48" height="9" rx="4" fill="#ff060a" />
            <rect x="26" y="61" width="32" height="9" rx="4" fill="#ff5c60" />
          </svg>
          <span class="font-semibold text-[15px] tracking-tight">APE</span>
        </RouterLink>

        <!-- desktop nav -->
        <nav class="hidden md:flex items-center gap-1">
          <RouterLink v-for="n in navItems" :key="n.to" :to="n.to" :class="navClass(n.to, n.exact)">
            <component :is="n.icon" class="h-4 w-4" />
            {{ n.label }}
          </RouterLink>
        </nav>

        <!-- right actions -->
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="hidden md:inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition"
            :title="`Theme: ${themeLabel}, click to change`"
            @click="cycleTheme"
          >
            <SparklesIcon class="h-3.5 w-3.5" /> {{ themeLabel }}
          </button>
          <AccountMenu v-if="getAccessToken()" class="hidden md:block" />
          <RouterLink
            v-if="!isChatRoute"
            to="/app/chat"
            class="btn-premium hidden sm:inline-flex items-center gap-1.5 h-8 px-3.5 rounded-md text-[13px] font-medium text-primary-foreground border border-red-400/15"
          >
            Open chat
          </RouterLink>
          <!-- mobile menu toggle -->
          <button
            class="md:hidden inline-flex h-9 w-9 items-center justify-center rounded-lg border hover:bg-muted/50"
            @click="showMobileNav = !showMobileNav"
            aria-label="Toggle navigation"
          >
            <Bars3Icon class="h-4 w-4" />
          </button>
        </div>
      </div>

      <!-- mobile dropdown -->
      <div v-if="showMobileNav" class="md:hidden border-t glass-panel">
        <nav class="max-w-7xl mx-auto px-4 py-3 grid gap-1.5">
          <RouterLink
            v-for="n in navItems" :key="'m-' + n.to" :to="n.to" :class="navClass(n.to, n.exact)"
            @click="showMobileNav = false"
          >
            <component :is="n.icon" class="h-4 w-4" /> {{ n.label }}
          </RouterLink>
          <div class="flex items-center gap-2 pt-2 mt-1 border-t">
            <button type="button" class="flex-1 inline-flex items-center justify-center gap-1.5 rounded-lg border px-3 py-2 text-sm text-muted-foreground hover:text-foreground" @click="cycleTheme">
              <SparklesIcon class="h-4 w-4" /> Theme: {{ themeLabel }}
            </button>
            <button v-if="getAccessToken()" type="button" class="inline-flex items-center justify-center gap-1.5 rounded-lg border px-3 py-2 text-sm text-muted-foreground hover:text-foreground" @click="logout">
              <ArrowRightOnRectangleIcon class="h-4 w-4" /> Sign out
            </button>
          </div>
        </nav>
      </div>
    </header>

    <!-- ===================== CONTENT ===================== -->
    <main class="relative z-10 flex-1 min-h-0 flex flex-col" :class="isChatRoute ? 'overflow-hidden' : 'overflow-y-auto'">
      <section
        class="flex-1 min-h-0 flex flex-col"
        :class="isChatRoute ? 'p-1 lg:p-2 overflow-hidden' : 'p-0'"
      >
        <RouterView />
      </section>
    </main>
  </div>
</template>
