<!--
  ExplainCard — the "every answer explains itself" mockup, made live. Cycles
  through real scenarios (comparison table → bullet summary → one-liner), each
  carrying its own chips: format, explore/exploit, intent, and banked reward.
  Body + chips cross-fade on every turn. Reduced-motion freezes on the first.
-->
<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { HandThumbUpIcon, HandThumbDownIcon } from '@/components/icons'

type Scene = {
  fmt: 'table' | 'bullets' | 'oneline'
  format: string; method: string; methodCls: string; intent: string; reward: string
  lead: string
}
const scenes: Scene[] = [
  { fmt: 'table', format: 'comparison table', method: 'learned · memory', methodCls: 'ape-chip-pos', intent: 'Comparison', reward: '+1.0 reward', lead: "Here's how the two plans compare on what matters:" },
  { fmt: 'bullets', format: 'bullet summary', method: 'learned · memory', methodCls: 'ape-chip-pos', intent: 'Explanation', reward: '+0.8 reward', lead: 'The trade-off in three points:' },
  { fmt: 'oneline', format: 'one-liner', method: 'exploring', methodCls: 'ape-chip-redraw', intent: 'Decision', reward: '+0.4 reward', lead: 'Straight answer:' },
]

const i = ref(0)
const s = computed(() => scenes[i.value])
let timer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  timer = setInterval(() => { i.value = (i.value + 1) % scenes.length }, 3200)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="rounded-2xl border bg-card p-4 shadow-lg shadow-red-900/10">
    <!-- chips: format · method · intent · reward (cross-fade per turn) -->
    <div class="text-xs text-muted-foreground mb-2 flex items-center gap-1.5 flex-wrap min-h-[22px]">
      <span class="font-medium text-foreground/80 mr-0.5">Assistant</span>
      <Transition name="chips" mode="out-in">
        <div :key="i" class="inline-flex items-center gap-1.5 flex-wrap">
          <span class="ape-chip ape-chip-strategy">{{ s.format }}</span>
          <span class="ape-chip" :class="s.methodCls">{{ s.method }}</span>
          <span class="ape-chip">{{ s.intent }}</span>
          <span class="ape-chip ape-chip-pos">{{ s.reward }}</span>
        </div>
      </Transition>
    </div>

    <Transition name="lead" mode="out-in">
      <div :key="'l'+i" class="text-[13px] leading-relaxed text-foreground/90 mb-2.5">{{ s.lead }}</div>
    </Transition>

    <!-- body morphs with the chosen format -->
    <div class="body-slot">
      <Transition name="morph" mode="out-in">
        <!-- table -->
        <div v-if="s.fmt === 'table'" key="table" class="grid grid-cols-3 gap-x-3 gap-y-1.5 text-xs rounded-xl border bg-background/50 p-3">
          <div class="text-muted-foreground"></div><div class="font-medium text-center">HDHP</div><div class="font-medium text-center">Low deductible</div>
          <div class="text-muted-foreground">Premium</div><div class="text-center tabular-nums text-red-500">$210/mo</div><div class="text-center tabular-nums">$385/mo</div>
          <div class="text-muted-foreground">Deductible</div><div class="text-center tabular-nums">$3,200</div><div class="text-center tabular-nums text-red-500">$750</div>
          <div class="text-muted-foreground">HSA eligible</div><div class="text-center text-red-500">Yes</div><div class="text-center">No</div>
        </div>
        <!-- bullets -->
        <ul v-else-if="s.fmt === 'bullets'" key="bullets" class="text-xs rounded-xl border bg-background/50 p-3 space-y-2">
          <li class="flex gap-2"><span class="mt-1 h-1.5 w-1.5 rounded-sm bg-red-500 flex-none" />HDHP: <span class="text-foreground/90">$210/mo premium</span>, but a $3,200 deductible.</li>
          <li class="flex gap-2"><span class="mt-1 h-1.5 w-1.5 rounded-sm bg-red-500 flex-none" />Low-deductible: pricier monthly, far less risk up front.</li>
          <li class="flex gap-2"><span class="mt-1 h-1.5 w-1.5 rounded-sm bg-red-500 flex-none" />Healthy + want the HSA tax break? <span class="text-foreground/90">HDHP wins.</span></li>
        </ul>
        <!-- one-liner -->
        <div v-else key="oneline" class="text-sm font-medium text-foreground rounded-xl border bg-background/50 p-3.5 leading-relaxed">
          Go with the <span class="text-red-600">HDHP</span> — lower premium, and the HSA tax break wins long-term.
        </div>
      </Transition>
    </div>

    <div class="flex items-center gap-1.5 mt-3 pt-2.5 border-t border-border/50">
      <span class="text-[10px] text-muted-foreground mr-0.5">Rate this answer</span>
      <span class="ape-rate-btn is-active-up"><HandThumbUpIcon class="h-3.5 w-3.5" /></span>
      <span class="ape-rate-btn"><HandThumbDownIcon class="h-3.5 w-3.5" /></span>
      <span class="text-[10px] text-muted-foreground">scores this answer with your next message</span>
    </div>
  </div>
</template>

<style scoped>
.body-slot { position: relative; min-height: 96px; display: grid; align-items: center; }
.morph-enter-active, .morph-leave-active { transition: opacity 360ms cubic-bezier(0.16, 1, 0.3, 1), transform 360ms cubic-bezier(0.16, 1, 0.3, 1); }
.morph-enter-from { opacity: 0; transform: translateY(10px); }
.morph-leave-to { opacity: 0; transform: translateY(-10px); position: absolute; inset: 0; }
.chips-enter-active, .chips-leave-active { transition: opacity 240ms ease, transform 240ms ease; }
.chips-enter-from { opacity: 0; transform: translateY(4px); }
.chips-leave-to { opacity: 0; transform: translateY(-4px); }
.lead-enter-active, .lead-leave-active { transition: opacity 240ms ease; }
.lead-enter-from, .lead-leave-to { opacity: 0; }
</style>
