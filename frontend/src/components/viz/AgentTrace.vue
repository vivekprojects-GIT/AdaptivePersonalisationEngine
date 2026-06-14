<script setup lang="ts">
/** AgentTrace, a live LangGraph-style execution graph for the chat.
 *
 *  Shows the REAL pipeline as it runs: Understand → Reward → Select →
 *  Generate → Render. Nodes pulse while active, fill when done, and surface
 *  the actual telemetry (intent, banked reward, strategy + method, widget).
 *  The Reward node carries id="trace-reward-slot", the flying thumb chip
 *  lands there.
 */
import { computed } from 'vue'
import { BoltIcon } from '@/components/icons'

type TracePhase = 'idle' | 'classify' | 'reward' | 'select' | 'generate' | 'render' | 'done'

const props = defineProps<{
  phase: TracePhase
  intent?: string | null
  lane?: string | null
  signals?: string[]
  rewardApplied?: number | null
  strategy?: string | null
  method?: string | null
  hasWidget?: boolean
}>()

const ORDER: TracePhase[] = ['classify', 'reward', 'select', 'generate', 'render']

const idx = computed(() => {
  if (props.phase === 'idle') return -1
  if (props.phase === 'done') return ORDER.length
  return ORDER.indexOf(props.phase)
})

function status(i: number): 'idle' | 'active' | 'done' {
  if (idx.value === -1) return 'idle'
  if (i < idx.value) return 'done'
  if (i === idx.value) return 'active'
  return 'idle'
}

function pretty(s?: string | null) {
  return String(s || '').replace(/_/g, ' ')
}
function fmtReward(v?: number | null) {
  if (v == null) return ''
  const n = Number(v)
  return `${n > 0 ? '+' : ''}${n.toFixed(1)}`
}

const steps = computed(() => [
  {
    key: 'classify',
    label: 'Understand',
    sub: 'classify the message',
    detail: props.intent
      ? [{ text: props.intent, cls: '' }, ...(props.lane === 'widget_redraw' ? [{ text: 'visual redraw', cls: 'ape-chip-redraw' }] : [])]
      : [],
  },
  {
    key: 'reward',
    label: 'Reward',
    sub: 'score the last answer',
    detail: props.rewardApplied != null
      ? [{ text: `${fmtReward(props.rewardApplied)} banked`, cls: Number(props.rewardApplied) > 0 ? 'ape-chip-pos' : 'ape-chip-neg' }]
      : (props.signals?.length ? props.signals.map((s) => ({ text: pretty(s), cls: '' })) : []),
  },
  {
    key: 'select',
    label: 'Select',
    sub: 'APE picks the format',
    detail: props.strategy
      ? [{ text: pretty(props.strategy), cls: 'ape-chip-strategy' }, ...(props.method ? [{ text: pretty(props.method), cls: props.method === 'learned' ? 'ape-chip-pos' : 'ape-chip-redraw' }] : [])]
      : [],
  },
  {
    key: 'generate',
    label: 'Generate',
    sub: 'LLM writes in that shape',
    detail: [],
  },
  {
    key: 'render',
    label: 'Render',
    sub: 'governed components',
    detail: props.hasWidget ? [{ text: 'live widget', cls: 'ape-chip-strategy' }] : [],
  },
])
</script>

<template>
  <div class="rounded-2xl border bg-card/70 glass-panel p-4 h-full flex flex-col">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <BoltIcon class="h-3.5 w-3.5 text-primary" />
        <span class="text-sm font-semibold">Agent trace</span>
      </div>
      <span
        class="ape-chip"
        :class="phase === 'done' ? 'ape-chip-pos' : phase !== 'idle' ? 'ape-chip-strategy' : ''"
      >
        {{ phase === 'idle' ? 'waiting' : phase === 'done' ? 'complete' : 'running' }}
      </span>
    </div>

    <div class="flex-1 min-h-0 overflow-y-auto pr-1">
      <div v-for="(s, i) in steps" :key="s.key" class="relative pl-8 pb-5 last:pb-0">
        <!-- connector -->
        <div
          v-if="i < steps.length - 1"
          class="absolute left-[11px] top-6 bottom-0 w-px transition-colors duration-500"
          :class="status(i) === 'done' ? 'bg-primary/50' : 'bg-border'"
        />
        <!-- node dot -->
        <div
          :id="s.key === 'reward' ? 'trace-reward-slot' : undefined"
          class="absolute left-0 top-0.5 h-[23px] w-[23px] rounded-full border-2 flex items-center justify-center transition-all duration-400"
          :class="{
            'border-border bg-background/60': status(i) === 'idle',
            'border-primary bg-primary/15 trace-pulse': status(i) === 'active',
            'border-primary bg-primary': status(i) === 'done',
          }"
        >
          <svg v-if="status(i) === 'done'" viewBox="0 0 12 12" class="h-3 w-3" aria-hidden="true">
            <path d="M2.5 6.5 5 9l4.5-5.5" fill="none" stroke="var(--primary-foreground)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <span v-else-if="status(i) === 'active'" class="h-2 w-2 rounded-full bg-primary" />
        </div>

        <div>
          <div class="text-[13px] font-semibold leading-tight" :class="status(i) === 'idle' ? 'text-muted-foreground' : ''">
            {{ s.label }}
          </div>
          <div class="text-[10.5px] text-muted-foreground mt-0.5">{{ s.sub }}</div>
          <Transition name="trace-detail">
            <div v-if="s.detail.length" class="flex flex-wrap gap-1 mt-1.5">
              <span v-for="d in s.detail" :key="d.text" class="ape-chip" :class="d.cls">{{ d.text }}</span>
            </div>
          </Transition>
        </div>
      </div>
    </div>

    <p class="text-[10px] text-muted-foreground/70 mt-3 pt-3 border-t leading-relaxed">
      This is the real pipeline for every message, the same one call your own agents would make.
    </p>
  </div>
</template>

<style scoped>
@keyframes tracePulse {
  0%, 100% { box-shadow: 0 0 0 0 color-mix(in oklab, var(--primary) 45%, transparent); }
  50% { box-shadow: 0 0 0 7px transparent; }
}
.trace-pulse { animation: tracePulse 1.4s ease-out infinite; }

.trace-detail-enter-active { transition: opacity 320ms ease, transform 320ms cubic-bezier(0.22, 1, 0.36, 1); }
.trace-detail-enter-from { opacity: 0; transform: translateY(5px); }

@media (prefers-reduced-motion: reduce) {
  .trace-pulse { animation: none; }
}
</style>
