<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { Motion } from '@motionone/vue'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'
import WidgetSchemaRenderer from '@/components/WidgetRegistryRenderer.vue'
import AgentTrace from '@/components/viz/AgentTrace.vue'

type TracePhase = 'idle' | 'classify' | 'reward' | 'select' | 'generate' | 'render' | 'done'
import { getAccessToken, clearAccessToken, getGuestId } from '@/lib/auth'
import { showToast } from '@/lib/toast'
import { renderAssistantMarkdown } from '@/lib/renderMarkdown'
import { MOTION_BASE, animatePulse, killAnimationsOf } from '@/lib/motion'
import { downloadTextAsFile, prettifyJsonIfPossible } from '@/lib/downloadFile'
import { widgetToHtml } from '@/lib/exportWidgetHtml'
import {
  ArrowDownTrayIcon, BoltIcon, HandThumbUpIcon, HandThumbDownIcon,
  SparklesIcon, TrashIcon, ArrowTrendingUpIcon,
  Squares2X2Icon, CpuChipIcon,
} from '@/components/icons'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ((typeof location !== 'undefined' && /^(localhost|127.0.0.1)$/.test(location.hostname)) ? 'http://localhost:5051' : '')

/** FastAPI uses `detail`; our API uses `error`, normalize for user-visible messages. */
function formatApiErrorBody(d: Record<string, unknown>, fallback: string): string {
  const err = d.error
  if (typeof err === 'string' && err.trim()) return err.trim()
  const det = d.detail
  if (typeof det === 'string' && det.trim()) return det.trim()
  if (Array.isArray(det)) {
    const parts = det
      .map((item) => {
        if (item && typeof item === 'object' && 'msg' in item) {
          return String((item as { msg?: string }).msg || '').trim()
        }
        return ''
      })
      .filter(Boolean)
    if (parts.length) return parts.join('; ')
  }
  return fallback
}

async function readJsonWithFallback(res: Response): Promise<Record<string, unknown>> {
  const text = await res.text().catch(() => '')
  if (!text.trim()) return {}
  try {
    return JSON.parse(text) as Record<string, unknown>
  } catch {
    return { error: text.slice(0, 400) }
  }
}

/** Matches backend `_json_layout_is_only_numeric_index_arrays` (bogus tic-tac-toe "lines" as text). */
const NUMERIC_TUPLE_TEXT_RE = /^\s*\[\s*\d+(\s*,\s*\d+)*\s*\]\s*$/

function schemaIsOnlyNumericTupleText(wSch: string): boolean {
  const s = wSch.trim()
  if (!s.startsWith('{')) return false
  try {
    const o = JSON.parse(s) as { layout?: unknown }
    const layout = o.layout
    if (!Array.isArray(layout) || layout.length < 2) return false
    for (const item of layout) {
      // Bare numeric array layout items (raw stream form, e.g. [0,1,2]) count as tuple junk.
      if (Array.isArray(item)) {
        if (!item.every((n) => typeof n === 'number')) return false
        continue
      }
      if (!item || typeof item !== 'object') return false
      const rec = item as Record<string, unknown>
      if (String(rec.type || '').toLowerCase() !== 'text') return false
      if (!NUMERIC_TUPLE_TEXT_RE.test(String(rec.content ?? ''))) return false
    }
    return true
  } catch {
    return false
  }
}

/** Drop useless index-array "widgets" (e.g. bare [0,1,2] tuples) that aren't real content. */
function recoverWidgetFromStreamIfDegenerate(cur: ChatMessage) {
  const sch = String(cur.widgetSchema || '').trim()
  if (schemaIsOnlyNumericTupleText(sch)) cur.widgetSchema = ''
}

const isStreaming = ref(false)

/* ----- Agent trace (LangGraph-style live pipeline panel) ------------------
 * Phases advance with REAL events: send → classify; timers walk through
 * reward/select while the server works (those stages genuinely run then);
 * the SSE 'start' event carries the actual telemetry → generate; widget
 * events → render; done → complete.                                        */
const trace = ref<{
  phase: TracePhase
  intent: string | null
  lane: string | null
  signals: string[]
  rewardApplied: number | null
  strategy: string | null
  method: string | null
  hasWidget: boolean
}>({
  phase: 'idle', intent: null, lane: null, signals: [],
  rewardApplied: null, strategy: null, method: null, hasWidget: false,
})
let traceTimers: ReturnType<typeof setTimeout>[] = []

function traceStart() {
  traceTimers.forEach(clearTimeout)
  trace.value = {
    phase: 'classify', intent: null, lane: null, signals: [],
    rewardApplied: null, strategy: null, method: null, hasWidget: false,
  }
  traceTimers = [
    setTimeout(() => { if (trace.value.phase === 'classify') trace.value.phase = 'reward' }, 800),
    setTimeout(() => { if (trace.value.phase === 'reward') trace.value.phase = 'select' }, 1500),
  ]
}
function traceTelemetry(ape?: ApeMeta) {
  traceTimers.forEach(clearTimeout)
  if (ape) {
    trace.value.intent = ape.intent && ape.intent !== 'unmapped' ? ape.intent : (ape.intent || null)
    trace.value.lane = ape.lane ?? null
    trace.value.signals = ape.signals_sent || []
    trace.value.rewardApplied = ape.reward_applied ?? null
    trace.value.method = ape.selection_method ?? null
  }
  trace.value.phase = 'generate'
}
function traceDone() {
  traceTimers.forEach(clearTimeout)
  trace.value.phase = 'done'
}
const streamStatus = ref('')
const healthOk = ref<boolean | null>(null)

/** Per-turn APE telemetry from the backend (`ctx["ape"]` in server.py). */
type ApeMeta = {
  served_by_ape?: boolean
  reason?: string
  turn_id?: string | null
  reward_applied?: number | null
  selection_method?: string | null
  intent?: string
  lane?: string
  signals_sent?: string[]
}

type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
  widgetSchema?: string
  widgetHeight?: number
  widgetStream?: string
  widgetStreaming?: boolean
  widgetMode?: 'json' | ''
  /** APE: the text strategy used for THIS answer. */
  strategy?: string
  /** APE: telemetry for the call that produced THIS answer. */
  ape?: ApeMeta
  /** APE: reward banked LATER for this answer (retro-attached when the next turn reports it). */
  rewardBanked?: number | null
  rewardSignals?: string[]
  /** Local thumbs state ('' = not rated). */
  rated?: 'up' | 'down' | ''
  /** True briefly when the answer finishes, drives the spring-in. */
  justLanded?: boolean
}

/** Successful `/api/chat` JSON (after error checks). */
type ChatApiSuccess = {
  response?: string
  widget_schema?: string
  widget_height?: number
  elapsed?: number
  strategy?: string
  ape?: ApeMeta
}

const messages = ref<ChatMessage[]>([])
const input = ref('')
const sending = ref(false)

const adaptiveScrollEl = ref<HTMLDivElement | null>(null)

const adaptiveStickToBottom = ref(true)
const streamPulseEl = ref<HTMLDivElement | null>(null)
const widgetGenerating = ref(false)
const widgetGeneratingIdx = ref<number | null>(null)
/** True while SSE is in widget phase (answer text may already be visible). */
const widgetStreamPhase = ref(false)

let healthTimer: ReturnType<typeof setInterval> | null = null

function authHeaders(): HeadersInit {
  const token = getAccessToken()
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) h.Authorization = `Bearer ${token}`
  // Stable per-browser identity, the backend uses it when no token is
  // present, so APE keeps learning per user without any login.
  h['X-Guest-Id'] = getGuestId()
  return h
}

/** Auth is optional now (guest mode): a stale token just degrades to guest.
 *  Clear it so the next request is clean, no redirect, no interruption. */
function handleAuthFailure(): boolean {
  clearAccessToken()
  showToast({ title: 'Continuing as guest', message: 'Your session expired; the chat keeps working.' })
  return true
}

async function fetchHealth() {
  try {
    const r = await fetch(`${API_BASE}/api/health`)
    healthOk.value = r.ok
  } catch {
    healthOk.value = false
  }
}

async function onClearChat() {
  if (!confirm('Clear all messages and widgets?')) return
  const res = await fetch(`${API_BASE}/api/conversation/clear`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  })
  if (!res.ok) {
    showToast({ title: 'Clear failed', message: 'Try again.' })
    return
  }
  messages.value = []
  showToast({ title: 'Chat cleared', message: 'Messages and widgets removed.' })
}

async function onReset() {
  if (!confirm('Reset your session? History for this account will be cleared.')) return
  const res = await fetch(`${API_BASE}/api/reset`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({}),
  })
  if (!res.ok) {
    showToast({ title: 'Reset failed', message: 'Try again.' })
    return
  }
  messages.value = []
  showToast({ title: 'Session reset', message: 'Your session was cleared.' })
}

async function runChatFallback(text: string, idx: number): Promise<boolean> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ message: text }),
  })
  if (res.status === 401) {
    handleAuthFailure()
    messages.value[idx].content = '⚠ Session expired, redirecting to login.'
    return false
  }
  const d = await readJsonWithFallback(res)
  if (!res.ok || d.error || d.detail) {
    messages.value[idx].content = `⚠ ${formatApiErrorBody(d, `Adaptive request failed (${res.status})`)}`
    return false
  }
  const payload = d as ChatApiSuccess
  const cur = messages.value[idx]
  applyApeMeta(idx, payload.strategy, payload.ape)
  cur.content = cleanAssistantText(
    typeof payload.response === 'string' ? payload.response : String(payload.response ?? ''),
  )
  cur.widgetSchema = typeof payload.widget_schema === 'string' ? payload.widget_schema : ''
  if (schemaIsOnlyNumericTupleText(cur.widgetSchema)) cur.widgetSchema = ''
  cur.widgetHeight = payload.widget_height ? Number(payload.widget_height) : 420
  return true
}

/** Store APE telemetry on the current answer; retro-attach the banked reward
 *  to the PREVIOUS assistant answer (that's the turn it actually scored). */
function applyApeMeta(idx: number, strategy?: unknown, ape?: unknown) {
  const cur = messages.value[idx]
  if (!cur) return
  if (typeof strategy === 'string' && strategy) cur.strategy = strategy
  if (!ape || typeof ape !== 'object') return
  const meta = ape as ApeMeta
  cur.ape = meta
  if (meta.reward_applied != null) {
    for (let i = idx - 1; i >= 0; i--) {
      const prev = messages.value[i]
      if (prev.role === 'assistant') {
        prev.rewardBanked = Number(meta.reward_applied)
        prev.rewardSignals = (meta.signals_sent || []).slice()
        break
      }
    }
  }
}

function prettyLabel(s?: string): string {
  return String(s || '').replace(/_/g, ' ')
}

/** Human label + tooltip for how APE picked this turn's format. */
function methodInfo(method?: string | null): { label: string; title: string } | null {
  switch (method) {
    case 'exploring':
      return {
        label: 'round-robin',
        title: 'Cold-start exploration, APE is giving each format a fair first try for this question type before it starts favoring winners.',
      }
    case 'learned':
      return {
        label: 'learned · memory',
        title: 'Exploitation, every format has been tried; APE picked the one with the best score so far (with a little exploration).',
      }
    case 'fallback':
      return {
        label: 'fallback',
        title: 'APE was unavailable for this turn, served the safe default format.',
      }
    default:
      return null
  }
}

function fmtReward(v?: number | null): string {
  if (v == null || Number.isNaN(Number(v))) return ''
  const n = Number(v)
  return `${n > 0 ? '+' : ''}${n.toFixed(1)}`
}

/** Index of the newest assistant message, the only one thumbs can target
 *  (APE rewards its latest pending turn; older messages would mis-attribute). */
const lastAssistantIdx = computed(() => {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].role === 'assistant') return i
  }
  return -1
})

/** Show the welcome screen until the user actually sends something. */
const showWelcome = computed(
  () => !isStreaming.value && !messages.value.some((m) => m.role === 'user'),
)

/** One-click starter prompts, each chosen to land in a different intent so the
 *  user immediately sees APE pick a different format. */
const examplePrompts = [
  { icon: Squares2X2Icon, intent: 'Comparison', text: 'Compare index funds vs individual stocks for a beginner' },
  { icon: CpuChipIcon, intent: 'Definitional', text: 'What is an expense ratio?' },
  { icon: ArrowTrendingUpIcon, intent: 'Decision', text: 'Should I pay off debt or invest first?' },
  { icon: SparklesIcon, intent: 'Instructional', text: 'How do I start a monthly budget?' },
]

function useExample(text: string) {
  if (sending.value || isStreaming.value) return
  input.value = text
  void onSend()
}

/** The reward chip physically flies from the thumb button to the Agent-trace
 *  Reward node (or the header APE chip as a fallback) and is absorbed there. */
function flyReward(fromEl: HTMLElement, direction: 'up' | 'down') {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  const target = document.querySelector('#trace-reward-slot') || document.querySelector('.ape-chip')
  if (!target) return
  const a = fromEl.getBoundingClientRect()
  const b = (target as HTMLElement).getBoundingClientRect()

  const chip = document.createElement('div')
  chip.className = 'fly-chip ' + (direction === 'up' ? 'fly-chip-pos' : 'fly-chip-neg')
  chip.textContent = direction === 'up' ? '+1.0' : '−1.0'
  chip.style.left = a.left + a.width / 2 + 'px'
  chip.style.top = a.top + a.height / 2 + 'px'
  document.body.appendChild(chip)

  const dx = b.left + b.width / 2 - (a.left + a.width / 2)
  const dy = b.top + b.height / 2 - (a.top + a.height / 2)
  chip
    .animate(
      [
        { transform: 'translate(-50%, -50%) scale(1)', opacity: 1 },
        { transform: `translate(calc(-50% + ${dx * 0.4}px), calc(-50% + ${dy * 0.4 - 40}px) ) scale(1.15)`, opacity: 1, offset: 0.45 },
        { transform: `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px)) scale(0.35)`, opacity: 0.1 },
      ],
      { duration: 750, easing: 'cubic-bezier(0.16, 1, 0.3, 1)' },
    )
    .onfinish = () => {
      chip.remove()
      // absorb pulse on the target
      ;(target as HTMLElement).animate(
        [{ transform: 'scale(1)' }, { transform: 'scale(1.35)' }, { transform: 'scale(1)' }],
        { duration: 360, easing: 'cubic-bezier(0.16, 1, 0.3, 1)' },
      )
    }
}

async function rateAnswer(direction: 'up' | 'down', idx: number, ev?: Event) {
  if (sending.value || isStreaming.value) return
  if (ev?.currentTarget) flyReward(ev.currentTarget as HTMLElement, direction)
  try {
    const res = await fetch(`${API_BASE}/api/rate`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ direction }),
    })
    if (res.status === 401) {
      handleAuthFailure()
      return
    }
    if (!res.ok) {
      const d = await readJsonWithFallback(res)
      throw new Error(formatApiErrorBody(d, `Rating failed (${res.status})`))
    }
    messages.value[idx].rated = direction
    showToast({
      title: direction === 'up' ? 'Thumbs up queued' : 'Thumbs down queued',
      message: 'It will score this answer when you send your next message.',
    })
  } catch (e) {
    showToast({ title: 'Rating failed', message: e instanceof Error ? e.message : String(e) })
  }
}

function handleSseEvent(evt: Record<string, unknown>, idx: number) {
  const cur = messages.value[idx]
  if (!evt?.type) return

  if (evt.type === 'start') {
    widgetStreamPhase.value = false
    streamStatus.value = 'Writing…'
    applyApeMeta(idx, evt.strategy, evt.ape)
    trace.value.strategy = typeof evt.strategy === 'string' ? evt.strategy : trace.value.strategy
    traceTelemetry(evt.ape as ApeMeta | undefined)
  }

  if (evt.type === 'response_delta') {
    widgetStreamPhase.value = false
    streamStatus.value = 'Streaming answer…'
    cur.content += String((evt as { delta?: string }).delta ?? '')
    requestAdaptiveAutoScroll()
  }

  if (evt.type === 'widget_start') {
    widgetStreamPhase.value = true
    streamStatus.value = 'Building interactive widget…'
    widgetGenerating.value = true
    widgetGeneratingIdx.value = idx
    cur.widgetStream = ''
    cur.widgetStreaming = true
    cur.widgetMode = ''
    trace.value.hasWidget = true
    trace.value.phase = 'render'
    requestAdaptiveAutoScroll()
  }

  if (evt.type === 'widget_delta') {
    widgetStreamPhase.value = true
    streamStatus.value = 'Building interactive widget…'
    widgetGenerating.value = true
    widgetGeneratingIdx.value = idx
    const delta = String((evt as { delta?: string }).delta ?? '')
    if (delta) {
      cur.widgetStream = (cur.widgetStream || '') + delta
      cur.widgetStreaming = true
      if (!cur.widgetMode) {
        const preview = cur.widgetStream.slice(0, 400).trim().toLowerCase()
        if (preview.startsWith('{') || preview.startsWith('[') || preview.startsWith('```json')) cur.widgetMode = 'json'
      }
      requestAdaptiveAutoScroll()
    }
  }

  if (evt.type === 'done') {
    streamStatus.value = ''
    widgetStreamPhase.value = false
    widgetGenerating.value = false
    widgetGeneratingIdx.value = null
    traceDone()
    // spring the landed answer card
    cur.justLanded = true
    setTimeout(() => { cur.justLanded = false }, 800)
    const e = evt as {
      response?: string
      widget_schema?: string
      widget_height?: number
      error?: string
      elapsed?: number
    }
    if (e.error) {
      cur.content = `⚠ ${e.error}`
      return
    }
    applyApeMeta(idx, (evt as Record<string, unknown>).strategy, (evt as Record<string, unknown>).ape)
    cur.content = cleanAssistantText(e.response ?? cur.content)
    cur.widgetSchema = typeof e.widget_schema === 'string' ? e.widget_schema.trim() : ''
    cur.widgetHeight = e.widget_height ? Number(e.widget_height) : 420
    cur.widgetStreaming = false

    recoverWidgetFromStreamIfDegenerate(cur)

    // If the server cleared the finalized schema but we already streamed JSON into
    // `widgetStream`, promote that stream so the panel still mounts (avoids the
    // "widget disappeared after completion" symptom).
    const stream = String(cur.widgetStream || '').trim()
    if (!cur.widgetSchema && stream && !schemaIsOnlyNumericTupleText(stream)) {
      cur.widgetSchema = stream
    }
    cur.widgetMode = cur.widgetSchema?.trim() ? 'json' : ''
  }
}

/** An action_row button was clicked, send its label as the next prompt. */
function onWidgetAction(text: string) {
  const t = String(text || '').trim()
  if (!t || sending.value || isStreaming.value) return
  input.value = t
  void onSend()
}

async function onSend() {
  const text = input.value.trim()
  if (!text || sending.value) return

  sending.value = true
  isStreaming.value = true
  widgetStreamPhase.value = false
  streamStatus.value = 'Thinking…'
  traceStart()
  // Each new turn anchors the pane to the latest messages.
  adaptiveStickToBottom.value = true

  messages.value.push({ role: 'user', content: text })
  const idx = messages.value.length
  messages.value.push({ role: 'assistant', content: '' })

  await nextTick()
  if (adaptiveScrollEl.value) scrollToBottom(adaptiveScrollEl.value)

  input.value = ''

  let finalized = false
  let fallbackUsed = false

  try {
    const resp = await fetch(`${API_BASE}/api/chat_stream`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ message: text }),
    })

    if (resp.status === 401) {
      handleAuthFailure()
      messages.value[idx].content = '⚠ Session expired, redirecting to login.'
      finalized = true
      return
    }

    if (!resp.ok) {
      if (resp.status === 401) {
        handleAuthFailure()
        messages.value[idx].content = '⚠ Session expired, redirecting to login.'
        finalized = true
        return
      }
      const d = await readJsonWithFallback(resp)
      throw new Error(formatApiErrorBody(d, `Stream request failed (${resp.status})`))
    }

    if (!resp.body) throw new Error('Streaming response missing body')

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buf = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      buf += decoder.decode(value, { stream: true })
      const blocks = buf.split('\n\n')
      buf = blocks.pop() || ''

      for (const block of blocks) {
        const dataLines = block
          .split('\n')
          .filter((ln) => ln.startsWith('data:'))
          .map((ln) => ln.slice(5).trimStart())

        if (!dataLines.length) continue

        let evt: Record<string, unknown> | null = null
        try {
          evt = JSON.parse(dataLines.join('\n'))
        } catch {
          continue
        }
        if (!evt) continue

        handleSseEvent(evt, idx)

        if (evt.type === 'done') {
          finalized = true
          const cur = messages.value[idx]
          // Redundant safety: promote streamed JSON if the done payload left the schema empty.
          const wSch = typeof (evt as { widget_schema?: string }).widget_schema === 'string' ? (evt as { widget_schema: string }).widget_schema.trim() : ''
          const stream = String(cur.widgetStream || '').trim()
          if (!wSch && stream && !schemaIsOnlyNumericTupleText(stream)) {
            cur.widgetSchema = stream
          }
          cur.widgetMode = cur.widgetSchema?.trim() ? 'json' : ''
          recoverWidgetFromStreamIfDegenerate(cur)
        }
      }
    }
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    if (!finalized) {
      try {
        const ok = await runChatFallback(text, idx)
        if (!ok) showToast({ title: 'Request failed', message: msg })
      } catch {
        messages.value[idx].content = `⚠ ${msg}`
        showToast({ title: 'Request failed', message: msg })
      }
      fallbackUsed = true
    }
  } finally {
    sending.value = false
    isStreaming.value = false
    streamStatus.value = ''
    widgetStreamPhase.value = false
    if (!finalized && !fallbackUsed) {
      try {
        const ok = await runChatFallback(text, idx)
        if (!ok) messages.value[idx].content ||= '⚠ Stream ended without final output.'
      } catch {
        messages.value[idx].content ||= '⚠ Stream ended without final output.'
      }
    }
  }
}

type HistoryPair = {
  user: string
  assistant: string
  widget_schema?: string
  widget_height?: number
}

function assistantFromHistoryPair(p: HistoryPair): ChatMessage {
  const wSch = String(p.widget_schema ?? '').trim()
  const wh = Number(p.widget_height) || 420
  const base: ChatMessage = {
    role: 'assistant',
    content: cleanAssistantText(p.assistant),
    widgetHeight: wh,
  }
  if (wSch && !schemaIsOnlyNumericTupleText(wSch)) {
    base.widgetSchema = wSch
    base.widgetMode = 'json'
  }
  return base
}

async function loadConversationHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/conversation?limit=20`, { headers: authHeaders() })
    if (!res.ok) return
    const d = await res.json().catch(() => ({}))

    const adaptiveHist = (d?.adaptive?.history ?? []) as HistoryPair[]

    messages.value = adaptiveHist.flatMap((p) => [
      { role: 'user' as const, content: p.user },
      assistantFromHistoryPair(p),
    ])
  } catch {
    // Non-blocking: chat still works even if history can't load.
  }

  // No placeholder message, an empty list shows the welcome screen instead.
}

onMounted(async () => {
  messages.value = []
  await loadConversationHistory()
  await nextTick()
  if (adaptiveScrollEl.value) scrollToBottom(adaptiveScrollEl.value)
  adaptiveStickToBottom.value = true

  fetchHealth()
  healthTimer = setInterval(fetchHealth, 30000)

  window.addEventListener('chat:control', onShellControl as EventListener)
})

onUnmounted(() => {
  if (healthTimer) clearInterval(healthTimer)
  killAnimationsOf(streamPulseEl.value)
  window.removeEventListener('chat:control', onShellControl as EventListener)
})

function onShellControl(e: Event) {
  const action = String((e as CustomEvent).detail?.action ?? '')
  if (action === 'clear-chat') {
    void onClearChat()
    return
  }
  if (action === 'reset') {
    void onReset()
  }
}

watch(
  () => messages.value.length,
  () => {
    nextTick(() => {
      if (adaptiveScrollEl.value && adaptiveStickToBottom.value) scrollToBottom(adaptiveScrollEl.value)
    })
  },
)

watch(isStreaming, (v) => {
  if (v) animatePulse(streamPulseEl.value)
  else killAnimationsOf(streamPulseEl.value)
})

/**
 * Strip any widget JSON the model leaked into the prose <RESPONSE>. The response is
 * meant to be human text only, JSON must NEVER reach the UI. Handles fenced blocks and
 * bare objects/arrays (balanced or truncated mid-stream).
 */
function stripLeakedJson(text: string): string {
  let s = text
  // 1) fenced code blocks whose content looks like widget JSON
  s = s.replace(/```[\w-]*\s*([\s\S]*?)```/g, (m, inner) => {
    const t = String(inner).trim()
    return /^[[{]/.test(t) && /"(?:type|layout|items|tone|series|chart|version)"/.test(t) ? '' : m
  })
  // 2) bare JSON widget/block blobs, balance-match (string-aware); truncated → cut to end
  const opener = /[{[]/g
  let match: RegExpExecArray | null
  while ((match = opener.exec(s)) !== null) {
    const start = match.index
    const head = s.slice(start, start + 400)
    if (!/"(?:type|layout|version)"\s*:/.test(head)) continue
    const open = s[start]
    const close = open === '{' ? '}' : ']'
    let depth = 0
    let inStr = false
    let esc = false
    let j = start
    for (; j < s.length; j++) {
      const ch = s[j]
      if (inStr) {
        if (esc) esc = false
        else if (ch === '\\') esc = true
        else if (ch === '"') inStr = false
      } else if (ch === '"') inStr = true
      else if (ch === open) depth++
      else if (ch === close) {
        depth--
        if (depth === 0) {
          j++
          break
        }
      }
    }
    const end = depth !== 0 ? s.length : j // unbalanced (truncated) → remove to end
    s = s.slice(0, start) + s.slice(end)
    opener.lastIndex = start
  }
  return s
}

function cleanAssistantText(raw: string | undefined | null) {
  const s = String(raw ?? '')
  const noWidgetBlock = s.replace(/<WIDGET>[\s\S]*?<\/WIDGET>/gi, '')
  const noTags = noWidgetBlock.replace(/<\/?WIDGET>/gi, '')
  return stripLeakedJson(noTags).trim()
}

// Vanguard "can't visualize this" notes: the model emits a NOTE line which we
// surface as a red callout (and strip from the prose body). Tolerant of the
// markdown the model may wrap it in: `NOTE:`, `**Note:**`, `> Note:`, `- Note:`.
function noteOf(line: string): string | null {
  // Strip leading blockquote / list / emphasis markers, then require "note:".
  const lead = line.replace(/^[\s>*_~`-]+/, '')
  const m = lead.match(/^note\s*[:\-—]\s*(.+)$/i)
  if (!m) return null
  // Remove stray emphasis markers from the message text.
  return m[1].replace(/\*\*/g, '').replace(/^[*_\s]+|[*_\s]+$/g, '').trim()
}

function extractNotes(text: string | undefined | null): string[] {
  return String(text ?? '')
    .split('\n')
    .map(noteOf)
    .filter((n): n is string => !!n)
}

function stripNotes(text: string | undefined | null): string {
  return String(text ?? '')
    .split('\n')
    .filter((l) => noteOf(l) === null)
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

/**
 * While the last assistant message is still receiving *answer* tokens, show plain text so half-written
 * markdown/tables do not flash. Once the server signals widget loading (`widgetGenerating`), the answer
 * text is complete, switch to markdown and show the compact widget loader below.
 */
function assistantStreamPlain(idx: number): boolean {
  const m = messages.value[idx]
  const last = idx === messages.value.length - 1
  const inWidgetWait =
    widgetGenerating.value && widgetGeneratingIdx.value === idx
  return Boolean(
    isStreaming.value && last && m?.role === 'assistant' && !inWidgetWait,
  )
}

function isNearBottom(el: HTMLElement, thresholdPx = 140): boolean {
  return el.scrollHeight - el.scrollTop - el.clientHeight < thresholdPx
}

function scrollToBottom(el: HTMLElement) {
  el.scrollTop = el.scrollHeight
}

let scrollRaf: number | null = null
function requestAdaptiveAutoScroll() {
  if (scrollRaf != null) return
  scrollRaf = window.requestAnimationFrame(() => {
    scrollRaf = null
    if (!adaptiveScrollEl.value) return
    if (!adaptiveStickToBottom.value) return
    scrollToBottom(adaptiveScrollEl.value)
  })
}

function onAdaptiveScroll() {
  if (!adaptiveScrollEl.value) return
  adaptiveStickToBottom.value = isNearBottom(adaptiveScrollEl.value)
}

function widgetDownloadBase(_m: ChatMessage, idx: number): string {
  return `widget-adaptive-${idx + 1}`
}

function downloadWidgetJson(jsonStr: string, base: string) {
  const body = prettifyJsonIfPossible(String(jsonStr || '').trim())
  if (!body) {
    showToast({ title: 'Nothing to download', message: 'Widget JSON is empty.' })
    return
  }
  downloadTextAsFile(body, `${base}.json`, 'application/json;charset=utf-8')
}

// Turn-level widget downloads (shown next to Helpful / Not helpful).
function downloadWidgetJsonFor(m: ChatMessage, idx: number) {
  downloadWidgetJson(String(m.widgetSchema || ''), widgetDownloadBase(m, idx))
}
function downloadWidgetHtmlFor(m: ChatMessage, idx: number) {
  const raw = String(m.widgetSchema || '').trim()
  if (!raw) {
    showToast({ title: 'Nothing to download', message: 'Widget is empty.' })
    return
  }
  try {
    const html = widgetToHtml(raw, (m.content || 'Widget').slice(0, 80))
    downloadTextAsFile(html, `${widgetDownloadBase(m, idx)}.html`, 'text/html;charset=utf-8')
  } catch {
    showToast({ title: 'Export failed', message: 'Could not build HTML.' })
  }
}
</script>

<template>
  <div class="h-full min-h-0 w-full min-w-0 overflow-hidden flex gap-3">
  <div class="flex-1 min-w-0 h-full min-h-0 grid grid-rows-[auto_minmax(0,1fr)_auto] gap-2">
    <div class="flex flex-wrap items-center gap-2 justify-between min-h-0">
      <div class="flex items-center gap-3">
        <h1 class="text-lg font-semibold tracking-tight">Chat</h1>
        <span
          class="inline-flex items-center gap-2 text-[11px] text-muted-foreground rounded-full border bg-background/60 px-2.5 py-1"
          :title="healthOk === false ? 'API unreachable' : 'API health'"
        >
          <span
            class="h-2 w-2 rounded-full shrink-0"
            :class="{
              'bg-violet-500': healthOk === true,
              'bg-red-500': healthOk === false,
              'bg-cyan-500 animate-pulse': healthOk === null,
            }"
          />
          {{ healthOk === false ? 'offline' : healthOk === true ? 'online' : 'checking…' }}
        </span>
      </div>
      <div class="flex items-center gap-1.5">
        <button
          type="button"
          class="inline-flex items-center gap-1.5 text-[12px] font-medium rounded-lg border px-3 py-1.5 text-muted-foreground hover:text-foreground hover:bg-muted/60 transition disabled:opacity-40"
          title="Start a fresh chat (keeps what APE has learned)"
          :disabled="isStreaming || sending || !messages.length"
          @click="onClearChat"
        >
          <SparklesIcon class="h-3.5 w-3.5" /> New chat
        </button>
        <button
          type="button"
          class="inline-flex items-center gap-1.5 text-[12px] font-medium rounded-lg border px-3 py-1.5 text-muted-foreground hover:text-rose-600 hover:border-rose-300/60 hover:bg-rose-500/5 transition disabled:opacity-40"
          title="Reset this session, clears history and learning for this browser"
          :disabled="isStreaming || sending"
          @click="onReset"
        >
          <TrashIcon class="h-3.5 w-3.5" /> Reset
        </button>
      </div>
    </div>

    <div class="grid gap-2 min-h-0 min-w-0 overflow-hidden items-stretch lg:grid-cols-1 xl:grid-cols-1">
      <Card class="flex flex-col min-h-0 min-w-0 overflow-hidden shadow-sm">
        <div
          class="px-3 py-2 border-b text-[11px] font-semibold text-muted-foreground uppercase tracking-wide flex items-center justify-between gap-2 flex-wrap"
        >
          <div class="flex items-center gap-2 min-w-0">
            <span>Adaptive</span>
            <span class="text-[10px] font-medium px-2 py-0.5 rounded-full border bg-background/60 shrink-0">Components</span>
            <span
              class="ape-chip ape-chip-strategy shrink-0"
              title="Text format is chosen per user + intent by APE's adaptive memory and learns from your reactions"
            >
              <BoltIcon class="h-3 w-3" />
              APE
            </span>
          </div>
          <div class="flex items-center gap-2 ml-auto">
          <div
            v-if="isStreaming"
            class="flex items-center gap-2 normal-case font-normal text-[11px] rounded-full px-2.5 py-1.5 border max-w-[min(100%,20rem)] transition-colors"
            :class="
              widgetStreamPhase
                ? 'border-cyan-500/45 bg-cyan-500/12 text-cyan-900 dark:text-cyan-100 shadow-sm shadow-black/20'
                : 'border-border/80 bg-muted/50 text-foreground/80'
            "
          >
            <span class="relative flex h-2 w-2 shrink-0">
              <span
                v-if="widgetStreamPhase"
                class="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-70"
              />
              <span
                class="relative inline-flex rounded-full h-2 w-2"
                :class="widgetStreamPhase ? 'bg-cyan-500' : 'bg-primary'"
              />
            </span>
            <span class="truncate">{{ streamStatus || 'Working…' }}</span>
          </div>
          </div>
        </div>
        <div
          ref="adaptiveScrollEl"
          class="chat-messages chat-pane-scroll flex-1 min-h-0 overflow-y-auto p-2.5 space-y-2 overscroll-contain scrollbar-gutter-stable"
          @scroll="onAdaptiveScroll"
        >
          <!-- Welcome / empty state -->
          <div
            v-if="showWelcome"
            class="h-full min-h-[60%] flex flex-col items-center justify-center text-center px-4 py-10 select-none"
          >
            <div class="relative mb-5">
              <div class="orb orb-cyan orb-float-a h-28 w-28 -top-6 -left-8 opacity-40" />
              <div class="orb orb-violet orb-float-b h-28 w-28 -bottom-6 -right-8 opacity-40" />
              <div class="relative h-16 w-16 rounded-2xl bg-gradient-to-br from-violet-500/20 to-violet-500/12 border border-primary/30 flex items-center justify-center">
                <BoltIcon class="h-7 w-7 text-primary" />
              </div>
            </div>
            <h2 class="text-xl font-semibold tracking-tight">Ask anything</h2>
            <p class="text-sm text-muted-foreground mt-1.5 max-w-md leading-relaxed">
              APE picks the best format for your question, then learns from how you react.
              Try one of these to see it choose a different shape each time:
            </p>
            <div class="grid sm:grid-cols-2 gap-2.5 mt-6 w-full max-w-xl">
              <button
                v-for="ex in examplePrompts"
                :key="ex.text"
                type="button"
                class="group text-left rounded-xl border bg-card/70 glass-panel p-3.5 tilt-3d tilt-hover transition"
                @click="useExample(ex.text)"
              >
                <div class="flex items-center gap-2 mb-1.5">
                  <span class="h-7 w-7 rounded-lg bg-primary/12 border border-primary/25 flex items-center justify-center shrink-0">
                    <component :is="ex.icon" class="h-3.5 w-3.5 text-primary" />
                  </span>
                  <span class="ape-chip">{{ ex.intent }}</span>
                </div>
                <div class="text-sm text-foreground/90 group-hover:text-foreground leading-snug">{{ ex.text }}</div>
              </button>
            </div>
          </div>

          <Motion
            v-for="(m, idx) in messages"
            :key="'a-' + idx"
            tag="div"
            class="w-full max-w-[860px] mx-auto space-y-1.5 premium-reveal border-t border-border/60 pt-5 mt-2 first:border-t-0 first:pt-0 first:mt-0"
            :class="m.role === 'user' ? 'is-user-turn' : 'is-assistant-turn'"
            :initial="{ opacity: 0, y: 10 }"
            :animate="{ opacity: 1, y: 0 }"
            :transition="{ ...MOTION_BASE, delay: idx * 0.03 }"
          >
            <div class="flex" :class="m.role === 'user' ? 'justify-end' : 'justify-start'">
              <div
                class="max-w-[99%] md:max-w-[96%] rounded-2xl border px-3 py-2 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/25"
                :class="[
                  m.role === 'user' ? 'bg-gradient-to-br from-primary/14 via-primary/8 to-accent/10 border-primary/25' : 'bg-card card-sheen',
                  m.justLanded ? 'spring-in' : '',
                ]"
              >
                <div class="text-xs text-muted-foreground mb-1 flex items-center gap-1.5 flex-wrap">
                  <span class="font-medium text-foreground/80 mr-0.5">{{ m.role === 'user' ? 'You' : 'Assistant' }}</span>

                  <!-- APE telemetry chips (assistant turns only) -->
                  <template v-if="m.role === 'assistant'">
                    <span
                      v-if="m.strategy"
                      class="ape-chip ape-chip-strategy"
                      :title="m.ape?.served_by_ape
                        ? 'Response format selected by APE for this user + intent'
                        : 'Fallback format, APE was not consulted for this turn'"
                    >
                      <BoltIcon class="h-3 w-3" />
                      {{ prettyLabel(m.strategy) }}
                    </span>
                    <span
                      v-if="methodInfo(m.ape?.selection_method)"
                      class="ape-chip"
                      :class="m.ape?.selection_method === 'exploring'
                        ? 'ape-chip-redraw'
                        : m.ape?.selection_method === 'learned' ? 'ape-chip-pos' : ''"
                      :title="methodInfo(m.ape?.selection_method)?.title"
                    >
                      {{ methodInfo(m.ape?.selection_method)?.label }}
                    </span>
                    <span
                      v-if="m.ape?.intent && m.ape.intent !== 'unmapped'"
                      class="ape-chip"
                      title="Intent detected for this question"
                    >
                      {{ m.ape.intent }}
                    </span>
                    <span
                      v-if="m.ape?.lane === 'widget_redraw'"
                      class="ape-chip ape-chip-redraw"
                      title="Visual redraw: same data, new chart kind. APE was skipped, no reward recorded, memory untouched."
                    >
                      visual redraw
                    </span>
                    <Motion
                      v-if="m.rewardBanked != null"
                      tag="span"
                      class="ape-chip"
                      :class="m.rewardBanked > 0 ? 'ape-chip-pos' : m.rewardBanked < 0 ? 'ape-chip-neg' : ''"
                      :initial="{ opacity: 0, scale: 0.85 }"
                      :animate="{ opacity: 1, scale: 1 }"
                      :transition="MOTION_BASE"
                      :title="'Reward banked for this answer'
                        + (m.rewardSignals?.length ? ', from: ' + m.rewardSignals.map(prettyLabel).join(', ') : '')"
                    >
                      {{ fmtReward(m.rewardBanked) }} reward
                    </Motion>
                  </template>
                </div>
                <div class="leading-relaxed min-w-0">
                  <template
                    v-if="m.role === 'assistant' && isStreaming && idx === messages.length - 1 && !m.content.trim()"
                  >
                    <div class="typing-indicator" aria-label="Assistant is typing">
                      <span class="typing-dot" />
                      <span class="typing-dot" />
                      <span class="typing-dot" />
                    </div>
                  </template>
                  <template v-else-if="m.role === 'assistant' && assistantStreamPlain(idx)">
                    <div class="whitespace-pre-wrap">{{ cleanAssistantText(m.content) }}</div>
                  </template>
                  <template v-else-if="m.role === 'assistant'">
                    <div class="assistant-markdown" v-html="renderAssistantMarkdown(stripNotes(cleanAssistantText(m.content)))" />
                    <div
                      v-for="(n, ni) in extractNotes(cleanAssistantText(m.content))"
                      :key="'note-' + ni"
                      class="vanguard-note"
                    >
                      <strong>Note:</strong> {{ n }}
                    </div>
                  </template>
                  <template v-else>
                    <div class="whitespace-pre-wrap">{{ m.content }}</div>
                  </template>
                </div>

                <!-- Widget lives INSIDE the assistant response, text + chart as one card. -->
                <!-- "Building widget…" pill: visible the whole creation phase. -->
                <div
                  v-if="
                    m.role === 'assistant' &&
                    m.widgetStreaming &&
                    !(m.widgetSchema && String(m.widgetSchema).trim())
                  "
                  class="mt-2 inline-flex items-center gap-2 text-xs text-muted-foreground rounded-full border bg-background/60 px-3 py-1.5"
                >
                  <span class="relative flex h-2 w-2">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-70" />
                    <span class="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
                  </span>
                  Building widget…
                </div>

                <!-- ONE widget renderer (partial stream → final schema in place; no remount/flicker). -->
                <Motion
                  v-if="
                    m.role === 'assistant' &&
                    ((m.widgetSchema && String(m.widgetSchema).trim()) ||
                      (m.widgetStreaming && m.widgetStream && String(m.widgetStream).trim()))
                  "
                  tag="div"
                  class="mt-2"
                  :initial="{ opacity: 0, y: 12 }"
                  :animate="{ opacity: 1, y: 0 }"
                  :transition="MOTION_BASE"
                >
                  <WidgetSchemaRenderer
                    :key="'widget-' + idx"
                    :json-str="(m.widgetSchema && String(m.widgetSchema).trim()) ? m.widgetSchema : (m.widgetStream || '')"
                    :streaming="!(m.widgetSchema && String(m.widgetSchema).trim())"
                    :download-base="widgetDownloadBase(m, idx)"
                    :show-download="false"
                    @action="onWidgetAction"
                  />
                </Motion>

                <!-- Actions inside the response: widget downloads. -->
                <div
                  v-if="m.role === 'assistant' && m.widgetSchema && String(m.widgetSchema).trim()"
                  class="flex flex-wrap items-center gap-2 mt-2 pt-2 border-t border-border/50"
                >
                  <Button type="button" variant="outline" size="sm" class="h-6 px-2 text-[11px] gap-1" title="Download as interactive HTML" @click="downloadWidgetHtmlFor(m, idx)">
                    <ArrowDownTrayIcon class="h-3 w-3" /> HTML
                  </Button>
                  <Button type="button" variant="outline" size="sm" class="h-6 px-2 text-[11px] gap-1" title="Download widget JSON" @click="downloadWidgetJsonFor(m, idx)">
                    <ArrowDownTrayIcon class="h-3 w-3" /> JSON
                  </Button>
                </div>

                <!-- Rate this answer, newest completed answer only (APE rewards
                     its latest pending turn; thumbs on older answers would
                     mis-attribute). Queued via /api/rate, applied next turn. -->
                <div
                  v-if="m.role === 'assistant' && idx === lastAssistantIdx && !isStreaming && !sending
                    && m.content && !m.content.startsWith('⚠')"
                  class="flex flex-wrap items-center gap-1.5 mt-2"
                  :class="m.widgetSchema && String(m.widgetSchema).trim() ? '' : 'pt-2 border-t border-border/50'"
                >
                  <span class="text-[10px] text-muted-foreground mr-0.5">Rate this answer</span>
                  <button
                    type="button"
                    class="ape-rate-btn"
                    :class="{ 'is-active-up': m.rated === 'up' }"
                    :disabled="m.rated === 'up'"
                    title="Good answer, queued as a thumbs-up signal for APE (applies with your next message)"
                    aria-label="Thumbs up"
                    @click="rateAnswer('up', idx, $event)"
                  >
                    <HandThumbUpIcon class="h-3.5 w-3.5" />
                  </button>
                  <button
                    type="button"
                    class="ape-rate-btn"
                    :class="{ 'is-active-down': m.rated === 'down' }"
                    :disabled="m.rated === 'down'"
                    title="Poor answer, queued as a thumbs-down signal for APE (applies with your next message)"
                    aria-label="Thumbs down"
                    @click="rateAnswer('down', idx, $event)"
                  >
                    <HandThumbDownIcon class="h-3.5 w-3.5" />
                  </button>
                  <span v-if="m.rated" class="text-[10px] text-muted-foreground">
                    queued, scores this answer with your next message
                  </span>
                </div>

              </div>
            </div>
          </Motion>
        </div>
      </Card>

    </div>

    <form class="chat-input-shell shrink-0 pt-1 pb-1" @submit.prevent="onSend">
      <div class="max-w-[880px] mx-auto w-full">
        <div class="composer-shell rounded-2xl px-3 py-2 flex gap-2 items-center">
          <div class="flex-1 min-w-0">
            <Input
              v-model="input"
              class="w-full border-0 bg-transparent shadow-none focus-visible:ring-0 h-10 text-[15px]"
              placeholder="Ask anything, data questions become live charts…"
            />
          </div>
          <Button type="submit" :disabled="sending || !input.trim()" class="h-10 px-5 rounded-xl shrink-0">
            {{ sending ? 'Sending…' : 'Send →' }}
          </Button>
        </div>
        <div class="text-[10px] text-muted-foreground mt-1 px-2">
          APE picks the text format per question type, rate answers to teach it your preference
        </div>
      </div>
    </form>

  </div>

  <!-- ===== Agent trace rail (xl+), the live pipeline graph ===== -->
  <aside class="hidden xl:block w-[300px] shrink-0 h-full min-h-0 py-0.5">
    <AgentTrace
      :phase="trace.phase"
      :intent="trace.intent"
      :lane="trace.lane"
      :signals="trace.signals"
      :reward-applied="trace.rewardApplied"
      :strategy="trace.strategy"
      :method="trace.method"
      :has-widget="trace.hasWidget"
    />
  </aside>

  </div>
</template>

<style scoped>
.chat-pane-scroll {
  /* Explicit fallback height for browsers that mis-handle nested flex min-height. */
  height: var(--chat-pane-height, calc(100dvh - 14rem));
}

@media (min-width: 1024px) {
  .chat-pane-scroll {
    height: var(--chat-pane-height-lg, calc(100dvh - 15rem));
  }
}

.chat-input-shell {
  position: relative;
  background: color-mix(in oklab, var(--background) 84%, transparent);
  backdrop-filter: blur(8px);
  z-index: 10;
}

.typing-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 0;
}

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 9999px;
  background: linear-gradient(90deg, rgb(167 139 250), rgb(6 182 212));
  opacity: 0.55;
  animation: typingPulse 1.1s infinite ease-in-out;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.15s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes typingPulse {
  0%,
  80%,
  100% {
    transform: translateY(0);
    opacity: 0.45;
  }
  40% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

.widget-glow {
  animation: widgetPanelBreathe 1.55s ease-in-out infinite;
}

@keyframes widgetPanelBreathe {
  0%,
  100% {
    box-shadow: 0 1px 0 0 rgba(6, 182, 212, 0.14);
  }
  50% {
    box-shadow: 0 10px 36px -4px rgba(6, 182, 212, 0.38);
  }
}

/* v-html markdown: tables, lists, emphasis */
.assistant-markdown :deep(p) {
  margin: 0 0 0.65em;
}
.assistant-markdown :deep(p:last-child) {
  margin-bottom: 0;
}
/* Key figures (the model's **bold**) highlighted in the brand accent, like the analyst look. */
.assistant-markdown :deep(strong) {
  color: hsl(var(--primary));
  font-weight: 600;
}
/* Vanguard "can't visualize this" note, red callout. */
.vanguard-note {
  margin-top: 0.6rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.6rem;
  border: 1px solid hsl(0 72% 50% / 0.35);
  background: hsl(0 80% 55% / 0.08);
  color: hsl(0 70% 42%);
  font-size: 0.85rem;
  line-height: 1.45;
}
.vanguard-note :deep(strong),
.vanguard-note strong {
  color: hsl(0 72% 45%);
  font-weight: 700;
}
:global(.dark) .vanguard-note {
  color: hsl(0 85% 76%);
  border-color: hsl(0 72% 60% / 0.4);
  background: hsl(0 80% 55% / 0.12);
}
:global(.dark) .vanguard-note strong {
  color: hsl(0 85% 80%);
}
/* "### Analysis" → a compact uppercase section label. */
.assistant-markdown :deep(h1),
.assistant-markdown :deep(h2),
.assistant-markdown :deep(h3) {
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: hsl(var(--muted-foreground));
  margin: 0.85em 0 0.4em;
}
.assistant-markdown :deep(ul),
.assistant-markdown :deep(ol) {
  margin: 0.35em 0 0.65em;
  padding-left: 1.25rem;
}
.assistant-markdown :deep(ul) {
  list-style: disc;
}
.assistant-markdown :deep(ol) {
  list-style: decimal;
}
.assistant-markdown :deep(li) {
  margin: 0.15em 0;
}
.assistant-markdown :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
  margin: 0.5rem 0 0.75rem;
}
.assistant-markdown :deep(th),
.assistant-markdown :deep(td) {
  border: 1px solid hsl(var(--border));
  padding: 0.4rem 0.55rem;
  text-align: left;
  vertical-align: top;
}
.assistant-markdown :deep(th) {
  background: hsl(var(--muted) / 0.45);
  font-weight: 600;
}
.assistant-markdown :deep(tr:nth-child(even) td) {
  background: hsl(var(--muted) / 0.12);
}
.assistant-markdown :deep(a) {
  color: hsl(var(--primary));
  text-decoration: underline;
  text-underline-offset: 2px;
}
.assistant-markdown :deep(code) {
  font-size: 0.85em;
  padding: 0.1em 0.35em;
  border-radius: 0.25rem;
  background: hsl(var(--muted) / 0.5);
}
.assistant-markdown :deep(pre) {
  margin: 0.5rem 0;
  padding: 0.65rem 0.75rem;
  border-radius: 0.375rem;
  background: hsl(var(--muted) / 0.35);
  overflow-x: auto;
  font-size: 0.8125rem;
}
.assistant-markdown :deep(pre code) {
  padding: 0;
  background: transparent;
}
.assistant-markdown :deep(blockquote) {
  margin: 0.5rem 0;
  padding-left: 0.75rem;
  border-left: 3px solid hsl(var(--border));
  color: hsl(var(--muted-foreground));
}
</style>
