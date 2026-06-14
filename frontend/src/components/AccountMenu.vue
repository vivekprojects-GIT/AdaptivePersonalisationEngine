<script setup lang="ts">
/** Profile dropdown: avatar button -> account details + Settings + Sign out.
 *  Used in the landing nav and the app nav. Reads the signed-in user from
 *  /api/me; closes on outside-click or Escape. */
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getAccessToken, clearAccessToken } from '@/lib/auth'
import { clearSessionUsername } from '@/lib/sessionUser'
import { showToast } from '@/lib/toast'
import {
  ChatBubbleLeftRightIcon,
  Cog6ToothIcon,
  InformationCircleIcon,
  ArrowRightOnRectangleIcon,
  ChevronDownIcon,
} from '@/components/icons'

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ((typeof location !== 'undefined' && /^(localhost|127.0.0.1)$/.test(location.hostname)) ? 'http://localhost:5051' : '')

const open = ref(false)
const username = ref('')
const email = ref('')
const root = ref<HTMLElement | null>(null)

async function loadMe() {
  const token = getAccessToken()
  if (!token) return
  try {
    const r = await fetch(`${API_BASE}/api/me`, { headers: { Authorization: `Bearer ${token}` } })
    const d = await r.json().catch(() => ({}))
    if (r.ok) {
      username.value = d?.username || ''
      email.value = d?.email || ''
    }
  } catch {
    /* non-fatal */
  }
}

function go(path: string) {
  open.value = false
  router.push(path)
}

function logout() {
  open.value = false
  clearAccessToken()
  clearSessionUsername()
  showToast({ title: 'Signed out', message: 'See you soon.' })
  router.push('/')
}

function onDocClick(e: MouseEvent) {
  if (open.value && root.value && !root.value.contains(e.target as Node)) open.value = false
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') open.value = false
}

onMounted(() => {
  loadMe()
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onKey)
})
onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onKey)
})
</script>

<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="inline-flex items-center gap-1 rounded-lg border pl-1 pr-1.5 py-1 hover:bg-muted/50 transition cursor-pointer"
      :aria-expanded="open"
      aria-haspopup="menu"
      aria-label="Account menu"
      @click="open = !open"
    >
      <span class="h-7 w-7 rounded-md bg-primary/15 border border-primary/30 flex items-center justify-center text-[12px] font-semibold text-primary uppercase">
        {{ (username || 'U').charAt(0) }}
      </span>
      <ChevronDownIcon class="h-3.5 w-3.5 text-muted-foreground" />
    </button>

    <transition name="acct">
      <div
        v-if="open"
        class="absolute right-0 mt-2 w-60 rounded-xl border glass-panel shadow-lg p-1.5 z-[60]"
        role="menu"
      >
        <div class="px-3 py-2.5 flex items-center gap-2.5">
          <span class="h-9 w-9 rounded-lg bg-primary/15 border border-primary/30 flex items-center justify-center text-sm font-semibold text-primary uppercase shrink-0">
            {{ (username || 'U').charAt(0) }}
          </span>
          <div class="min-w-0">
            <div class="text-sm font-medium truncate">{{ username || 'Account' }}</div>
            <div class="text-xs text-muted-foreground truncate">{{ email }}</div>
          </div>
        </div>
        <div class="h-px bg-border my-1" />
        <button type="button" role="menuitem" class="w-full flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-foreground/90 hover:bg-muted/60 transition cursor-pointer" @click="go('/app/chat')">
          <ChatBubbleLeftRightIcon class="h-4 w-4 text-muted-foreground" /> Open the app
        </button>
        <button type="button" role="menuitem" class="w-full flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-foreground/90 hover:bg-muted/60 transition cursor-pointer" @click="go('/app/settings')">
          <Cog6ToothIcon class="h-4 w-4 text-muted-foreground" /> Settings
        </button>
        <button type="button" role="menuitem" class="w-full flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-foreground/90 hover:bg-muted/60 transition cursor-pointer" @click="go('/about')">
          <InformationCircleIcon class="h-4 w-4 text-muted-foreground" /> How it works
        </button>
        <div class="h-px bg-border my-1" />
        <button type="button" role="menuitem" class="w-full flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-destructive hover:bg-destructive/10 transition cursor-pointer" @click="logout">
          <ArrowRightOnRectangleIcon class="h-4 w-4" /> Sign out
        </button>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.acct-enter-active,
.acct-leave-active {
  transition: opacity 140ms ease, transform 140ms ease;
}
.acct-enter-from,
.acct-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}
</style>
