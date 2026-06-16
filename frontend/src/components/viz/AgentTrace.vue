<!--
  AgentTrace — a LangGraph-style execution graph: Understand → Reward → Select →
  Generate → Render. Nodes pulse while active, fill when done, surfacing real
  telemetry (intent, banked reward, strategy + method, widget).

  In the live chat it's driven by the `phase` prop. On the marketing page pass
  `autoplay` and it cycles the whole pipeline on a loop with demo telemetry that
  reveals stage-by-stage.
-->
<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { BoltIcon } from '@/components/icons'

type TracePhase = 'idle' | 'classify' | 'reward' | 'select' | 'generate' | 'render' | 'done'

const props = withDefaults(defineProps<{
  phase?: TracePhase
  intent?: string | null
  lane?: string | null
  signals?: string[]
  rewardApplied?: number | null
  strategy?: string | null
  method?: string | null
  hasWidget?: boolean
  autoplay?: boolean
}>(), { phase: 'idle', autoplay: false })

const ORDER: TracePhase[] = ['classify', 'reward', 'select', 'generate', 'render']

// --- autoplay: cycle the pipeline on a loop ---
const autoPhase = ref<TracePhase>('idle')
let t: ReturnType<typeof setTimeout> | null = null
const SCHEDULE: { p: TracePhase; ms: number }[] = [
  { p: 'classify', ms: 950 }, { p: 'reward', ms: 950 }, { p: 'select', ms: 1000 },
  { p: 'generate', ms: 1100 }, { p: 'render', ms: 950 }, { p: 'done', ms: 1900 }, { p: 'idle', ms: 650 },
]
function run(i: number) {
  const step = SCHEDULE[i % SCHEDULE.length]
  autoPhase.value = step.p
  t = setTimeout(() => run(i + 1), step.ms)
}

onMounted(() => {
  if (!props.autoplay) return
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { autoPhase.value = 'done'; return }
  run(0)
})
onUnmounted(() => { if (t) clearTimeout(t) })

// effective phase + telemetry (demo values when autoplaying)
const phase = computed<TracePhase>(() => (props.autoplay ? autoPhase.value : props.phase))
const intent = computed(() => (props.autoplay ? 'Comparison' : props.intent))
const rewardApplied = computed(() => (props.autoplay ? 1 : props.rewardApplied))
const strategy = computed(() => (props.autoplay ? 'comparison_table' : props.strategy))
const method = computed(() => (props.autoplay ? 'learned' : props.method))

const idx = computed(() => {
  if (phase.value === 'idle') return -1
  if (phase.value === 'done') return ORDER.length
  return ORDER.indexOf(phase.value)
})
function status(i: number): 'idle' | 'active' | 'done' {
  if (idx.value === -1) return 'idle'
  if (i < idx.value) return 'done'
  if (i === idx.value) return 'active'
  return 'idle'
}

function pretty(s?: string | null) { return String(s || '').replace(/_/g, ' ') }
function fmtReward(v?: number | null) {
  if (v == null) return ''
  const n = Number(v)
  return `${n > 0 ? '+' : ''}${n.toFixed(1)}`
}

const steps = computed(() => [
  { key: 'classify', label: 'Understand', sub: 'classify the message',
    detail: intent.value ? [{ text: intent.value, cls: '' }, ...(props.lane === 'widget_redraw' ? [{ text: 'visual redraw', cls: 'ape-chip-redraw' }] : [])] : [] },
  { key: 'reward', label: 'Reward', sub: 'score the last answer',
    detail: rewardApplied.value != null ? [{ text: `${fmtReward(rewardApplied.value)} banked`, cls: Number(rewardApplied.value) > 0 ? 'ape-chip-pos' : 'ape-chip-neg' }] : (props.signals?.length ? props.signals.map((s) => ({ text: pretty(s), cls: '' })) : []) },
  { key: 'select', label: 'Select', sub: 'APE picks the format',
    detail: strategy.value ? [{ text: pretty(strategy.value), cls: 'ape-chip-strategy' }, ...(method.value ? [{ text: pretty(method.value), cls: method.value === 'learned' ? 'ape-chip-pos' : 'ape-chip-redraw' }] : [])] : [] },
  { key: 'generate', label: 'Generate', sub: 'LLM writes in that shape', detail: [] },
  { key: 'render', label: 'Render', sub: 'governed components',
    detail: props.hasWidget ? [{ text: 'live widget', cls: 'ape-chip-strategy' }] : [] },
])
</script>

<template>
  <div class="rounded-2xl border bg-card/70 glass-panel p-4 h-full flex flex-col">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <BoltIcon class="h-3.5 w-3.5 text-primary" />
        <span class="text-sm font-semibold">Agent trace</span>
      </div>
      <span class="ape-chip" :class="phase === 'done' ? 'ape-chip-pos' : phase !== 'idle' ? 'ape-chip-strategy' : ''">
        {{ phase === 'idle' ? 'waiting' : phase === 'done' ? 'complete' : 'running' }}
      </span>
    </div>

    <div class="flex-1 min-h-0 overflow-y-auto pr-1">
      <div v-for="(s, i) in steps" :key="s.key" class="relative pl-8 pb-5 last:pb-0">
        <div v-if="i < steps.length - 1" class="absolute left-[11px] top-6 bottom-0 w-px transition-colors duration-500"
          :class="status(i) === 'done' ? 'bg-primary/50' : 'bg-border'" />
        <div :id="s.key === 'reward' ? 'trace-reward-slot' : undefined"
          class="absolute left-0 top-0.5 h-[23px] w-[23px] rounded-full border-2 flex items-center justify-center transition-all duration-400"
          :class="{
            'border-border bg-background/60': status(i) === 'idle',
            'border-primary bg-primary/15 trace-pulse': status(i) === 'active',
            'border-primary bg-primary': status(i) === 'done',
          }">
          <svg v-if="status(i) === 'done'" viewBox="0 0 12 12" class="h-3 w-3" aria-hidden="true">
            <path d="M2.5 6.5 5 9l4.5-5.5" fill="none" stroke="var(--primary-foreground)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <span v-else-if="status(i) === 'active'" class="h-2 w-2 rounded-full bg-primary" />
        </div>

        <div>
          <div class="text-[13px] font-semibold leading-tight transition-colors duration-300" :class="status(i) === 'idle' ? 'text-muted-foreground' : ''">
            {{ s.label }}
          </div>
          <div class="text-[10.5px] text-muted-foreground mt-0.5">{{ s.sub }}</div>
          <!-- chips reveal only once the stage is reached -->
          <Transition name="trace-detail">
            <div v-if="s.detail.length && status(i) !== 'idle'" class="flex flex-wrap gap-1 mt-1.5">
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
.trace-detail-enter-active { transition: opacity 320ms ease, transform 320ms cubic-bezier(0.16, 1, 0.3, 1); }
.trace-detail-enter-from { opacity: 0; transform: translateY(5px); }
.trace-detail-leave-active { transition: opacity 200ms ease; position: absolute; }
.trace-detail-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) { .trace-pulse { animation: none; } }
</style>
