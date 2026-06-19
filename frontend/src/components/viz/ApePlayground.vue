<script setup lang="ts">
/** ApePlayground, the landing page talks to the REAL engine.
 *
 *  Every click hits the live APE service through a sandboxed bandit user
 *  ("pg_<guest>"): "Run selection" creates a genuine turn, a thumb delivers a
 *  genuine reward AND triggers the next pick, and the scoreboard on the right
 *  is the actual bandit state (pulls, avg reward, live UCB) read back from
 *  the engine. Nothing is simulated.
 */
import { onMounted, ref } from 'vue'
import Button from '@/components/ui/Button.vue'
import CountUp from '@/components/viz/CountUp.vue'
import { getGuestId } from '@/lib/auth'
import { HandThumbUpIcon, HandThumbDownIcon } from '@/components/icons'
import { BoltIcon, ArrowPathIcon } from '@/components/icons'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ((typeof location !== 'undefined' && /^(localhost|127.0.0.1)$/.test(location.hostname)) ? 'http://localhost:5051' : '')

const INTENTS = ['Decision', 'Explanation', 'Comparison', 'Instructional', 'Definitional', 'Evaluation']

type Arm = { strategy: string; count: number; avg_reward: number; confidence: number }
type Result = { ok: boolean; reason: string; strategy: string; selection_method: string | null }

const intent = ref('Comparison')
const loading = ref(false)
const offline = ref(false)
const result = ref<Result | null>(null)
const arms = ref<Arm[]>([])
const picks = ref(0)
const resultKey = ref(0) // remount → spring-in replays

/* live proof-band stats */
const stats = ref<null | {
  total_turns: number; total_users: number; total_strategies: number; total_topics: number
  best_strategy: string | null; best_avg_reward: number; default_avg_reward: number
}>(null)

async function loadStats(retry = true) {
  try {
    const r = await fetch(`${API_BASE}/api/playground/stats`)
    const j = await r.json()
    if (j && j.ok) stats.value = j
    else if (retry) setTimeout(() => loadStats(false), 8000)
  } catch { /* band simply stays hidden */ }
}

function pickIntent(i: string) {
  if (loading.value || i === intent.value) return
  intent.value = i
  result.value = null
  arms.value = []
  picks.value = 0
}

async function run(signal?: 'thumbs_up' | 'thumbs_down') {
  if (loading.value) return
  loading.value = true
  try {
    const r = await fetch(`${API_BASE}/api/playground/turn`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Guest-Id': getGuestId() },
      body: JSON.stringify({ intent: intent.value, signal: signal || null }),
    })
    const j = await r.json()
    offline.value = !j.ok
    result.value = j
    arms.value = (j.arms || []).slice().sort((a: Arm, b: Arm) => b.confidence - a.confidence)
    picks.value += 1
    resultKey.value += 1
  } catch {
    offline.value = true
    result.value = null
  } finally {
    loading.value = false
  }
}

function pretty(s: string | null | undefined) {
  return (s || '').replace(/_/g, ' ')
}

const methodMeta: Record<string, { label: string; cls: string; note: string }> = {
  exploring: {
    label: 'exploring · fair trials',
    cls: 'border-zinc-400/30 bg-zinc-400/10 text-zinc-500',
    note: 'Cold start: every format gets one fair trial before scores decide.',
  },
  learned: {
    label: 'exploiting · learned',
    cls: 'border-red-400/30 bg-red-400/10 text-primary',
    note: 'Enough evidence: the strongest memory wins this pick.',
  },
  fallback: {
    label: 'degraded · fallback',
    cls: 'border-amber-400/30 bg-amber-400/10 text-amber-300',
    note: 'The engine degraded gracefully and a neutral format was served.',
  },
}

/* Plain-English description of each format. Kept here (not sent from the
 * engine) so the page never exposes the raw prompt directives. */
const formatDesc: Record<string, string> = {
  standard_llm: 'Whatever shape best fits the question.',
  decision_card: 'A clear verdict up top, with the reasoning beneath.',
  pros_cons_table: 'Pros and cons, side by side.',
  step_by_step_reasoning: 'The reasoning laid out step by step.',
  short_paragraph: 'A tight single paragraph.',
  bullet_summary: 'The key points as a clean bulleted list.',
  analogy_explanation: 'Explained through a simple analogy.',
  comparison_table: 'The options compared side by side in a table.',
  bullet_contrast: "Each option's points, set against each other.",
  numbered_steps: 'Numbered, do-this-then-that steps.',
  checklist: 'A checklist you can tick through.',
  phased_workflow: 'Grouped into clear, ordered phases.',
  one_liner: 'A single, direct sentence.',
  definition_plus_example: 'A definition, then a concrete example.',
  definition_with_pointer: 'A definition, plus where to go next.',
  statement_with_caveats: 'A direct take, with the caveats noted.',
  statement_with_actions: 'A direct take, with next actions.',
  three_section_review: 'A short header, body, and action.',
}

function barWidth(a: Arm): number {
  if (a.confidence >= 900) return 100
  const finite = arms.value.filter((x) => x.confidence < 900).map((x) => x.confidence)
  const max = Math.max(...finite, 0.0001)
  return Math.max(8, Math.round((a.confidence / max) * 100))
}

onMounted(() => loadStats())
</script>

<template>
  <div class="space-y-10">

    <!-- live proof band -->
    <div v-if="stats" v-reveal class="rounded-2xl border glass-panel bg-card/60 px-6 py-5">
      <div class="flex flex-wrap items-center gap-x-10 gap-y-4 justify-between">
        <div class="flex items-center gap-2 text-[11px] uppercase tracking-wider text-muted-foreground">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-60" />
            <span class="relative inline-flex rounded-full h-2 w-2 bg-red-400" />
          </span>
          live from the engine
        </div>
        <div class="flex flex-wrap gap-x-10 gap-y-3">
          <div>
            <div class="text-2xl font-semibold tabular-nums tracking-tight"><CountUp :end="stats.total_turns" /></div>
            <div class="text-[11px] text-muted-foreground">turns learned from</div>
          </div>
          <div>
            <div class="text-2xl font-semibold tabular-nums tracking-tight"><CountUp :end="stats.total_users" /></div>
            <div class="text-[11px] text-muted-foreground">users mapped</div>
          </div>
          <div>
            <div class="text-2xl font-semibold tabular-nums tracking-tight"><CountUp :end="stats.total_strategies" /></div>
            <div class="text-[11px] text-muted-foreground">formats in catalog</div>
          </div>
          <div>
            <div class="text-2xl font-semibold tabular-nums tracking-tight"><CountUp :end="stats.total_topics" /></div>
            <div class="text-[11px] text-muted-foreground">topics tracked</div>
          </div>
        </div>
        <div v-if="stats.best_strategy" class="text-[12px] text-muted-foreground max-w-[230px] leading-relaxed">
          <span class="text-foreground font-medium">{{ pretty(stats.best_strategy) }}</span> earns
          <span class="text-primary font-semibold tabular-nums">score {{ stats.best_avg_reward }}</span> vs
          <span class="tabular-nums">{{ stats.default_avg_reward }}</span> for one-size-fits-all prose.
        </div>
      </div>
    </div>

    <!-- playground -->
    <div class="grid lg:grid-cols-2 gap-6 items-start">

      <!-- left: controls + result -->
      <div v-reveal class="rounded-3xl border glass-panel bg-card/60 p-6 space-y-5">
        <div class="flex items-center justify-between">
          <div class="text-sm font-medium">1 · Pick an intent</div>
          <span class="text-[10px] text-muted-foreground border rounded-full px-2 py-0.5">sandboxed demo user</span>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="i in INTENTS"
            :key="i"
            type="button"
            class="rounded-full border px-3.5 py-2.5 sm:px-3 sm:py-1.5 text-[12px] transition-all cursor-pointer"
            :class="intent === i ? 'border-red-400/40 bg-red-500/15 text-foreground' : 'text-muted-foreground hover:text-foreground hover:border-border'"
            :aria-pressed="intent === i"
            @click="pickIntent(i)"
          >
            {{ i }}
          </button>
        </div>

        <div class="text-sm font-medium pt-1">2 · Ask the engine</div>
        <Button class="h-9 px-4 text-[13px] gap-2" :disabled="loading" @click="run()">
          <ArrowPathIcon v-if="loading" class="h-3.5 w-3.5 animate-spin" />
          <BoltIcon v-else class="h-3.5 w-3.5" />
          {{ picks === 0 ? 'Run a live selection' : 'Run it again' }}
        </Button>

        <div v-if="offline" class="rounded-xl border border-amber-400/25 bg-amber-400/5 p-4 text-[12.5px] text-muted-foreground">
          The live engine isn’t reachable right now, that’s the point of the design: chat keeps working on a neutral
          format and learning resumes when APE returns.
        </div>

        <div v-else-if="result" :key="resultKey" class="spring-in rounded-2xl border bg-background/40 p-5 space-y-3">
          <div class="flex items-center justify-between gap-3 flex-wrap">
            <div class="text-lg font-semibold tracking-tight capitalize">{{ pretty(result.strategy) }}</div>
            <span
              v-if="result.selection_method && methodMeta[result.selection_method]"
              class="rounded-full border px-2.5 py-1 text-[10.5px] font-medium"
              :class="methodMeta[result.selection_method].cls"
            >
              {{ methodMeta[result.selection_method].label }}
            </span>
          </div>
          <p v-if="result.selection_method && methodMeta[result.selection_method]" class="text-[12px] text-muted-foreground">
            {{ methodMeta[result.selection_method].note }}
          </p>
          <p v-if="formatDesc[result.strategy]" class="text-[12.5px] text-muted-foreground leading-relaxed border-l-2 border-red-400/30 pl-3">
            {{ formatDesc[result.strategy] }}
          </p>
          <div class="flex items-center gap-2 pt-1">
            <span class="text-[12px] text-muted-foreground mr-1">3 · Reward it, watch the next pick:</span>
            <button
              type="button"
              class="h-11 w-11 sm:h-8 sm:w-8 shrink-0 rounded-lg border flex items-center justify-center text-muted-foreground hover:text-red-400 hover:border-red-400/40 transition-colors cursor-pointer"
              aria-label="Reward this format (+1) and run the next selection"
              :disabled="loading"
              @click="run('thumbs_up')"
            >
              <HandThumbUpIcon class="h-4 w-4" />
            </button>
            <button
              type="button"
              class="h-11 w-11 sm:h-8 sm:w-8 shrink-0 rounded-lg border flex items-center justify-center text-muted-foreground hover:text-rose-400 hover:border-rose-400/40 transition-colors cursor-pointer"
              aria-label="Penalise this format (−1) and run the next selection"
              :disabled="loading"
              @click="run('thumbs_down')"
            >
              <HandThumbDownIcon class="h-4 w-4" />
            </button>
          </div>
        </div>

        <p v-else class="text-[12.5px] text-muted-foreground leading-relaxed">
          This is not a mock; the button calls the production engine. It tries every untried format once,
          then leans on what it has learned. Your real chat profile is untouched.
        </p>
      </div>

      <!-- right: live scoreboard -->
      <div v-reveal="120" class="rounded-3xl border glass-panel bg-card/60 p-6 space-y-4 min-h-[280px]" aria-live="polite">
        <!-- announced to screen readers after each live call -->
        <span class="sr-only">
          {{ result && !offline ? `The engine picked ${pretty(result.strategy)} via ${result.selection_method === 'learned' ? 'learned memory' : 'fair exploration'}.` : '' }}
        </span>
        <div class="flex items-center justify-between">
          <div class="text-sm font-medium">The engine’s scoreboard <span class="text-muted-foreground font-normal">· {{ intent }}</span></div>
          <span v-if="picks" class="text-[10px] text-muted-foreground tabular-nums">{{ picks }} live {{ picks === 1 ? 'call' : 'calls' }}</span>
        </div>

        <div v-if="!arms.length" class="text-[12.5px] text-muted-foreground leading-relaxed pt-2">
          Run a selection and the engine’s real per-format state appears here: pulls, the score each
          format has earned, and which one the engine picks next.
        </div>

        <TransitionGroup v-else name="pg-arm" tag="div" class="space-y-2.5">
          <div
            v-for="a in arms"
            :key="a.strategy"
            class="rounded-xl border p-3 transition-all duration-300"
            :class="result && a.strategy === result.strategy ? 'border-red-400/40 bg-red-500/[0.07]' : 'bg-background/30'"
          >
            <div class="flex items-center justify-between gap-2 mb-1.5">
              <div class="text-[12.5px] font-medium capitalize truncate">{{ pretty(a.strategy) }}</div>
              <div class="flex items-center gap-2 shrink-0 text-[10.5px] text-muted-foreground tabular-nums">
                <span v-if="result && a.strategy === result.strategy" class="text-primary font-semibold">← picked</span>
                <span>{{ a.count }} {{ a.count === 1 ? 'pull' : 'pulls' }}</span>
                <span>{{ a.count > 0 ? 'score ' + a.avg_reward.toFixed(2) : 'no evidence yet' }}</span>
              </div>
            </div>
            <div class="h-1.5 rounded-full bg-border/50 overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-700 ease-out"
                :class="a.confidence >= 900 ? 'bg-gradient-to-r from-zinc-400/60 to-zinc-300/40 pg-cold' : 'bg-gradient-to-r from-red-500 to-red-400'"
                :style="{ width: barWidth(a) + '%' }"
              />
            </div>
            <div v-if="a.confidence >= 900" class="mt-1 text-[10px] tabular-nums text-muted-foreground">
              untried · next in the rotation
            </div>
          </div>
        </TransitionGroup>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pg-arm-move { transition: transform 500ms cubic-bezier(0.16, 1, 0.3, 1); }
.pg-cold { animation: pgPulse 2.2s ease-in-out infinite; }
@keyframes pgPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.55; } }
@media (prefers-reduced-motion: reduce) {
  .pg-cold { animation: none; }
  .pg-arm-move { transition: none; }
}
</style>
