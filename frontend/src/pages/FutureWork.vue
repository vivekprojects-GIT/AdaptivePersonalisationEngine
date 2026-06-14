<script setup lang="ts">
import Button from '@/components/ui/Button.vue'
import {
  BoltIcon,
  ChatBubbleLeftRightIcon,
  ShieldCheckIcon,
  CpuChipIcon,
  ArrowTrendingUpIcon,
  Squares2X2Icon,
  SparklesIcon,
} from '@/components/icons'

/* Status vocabulary used across the roadmap. */
type Status = 'shipped' | 'progress' | 'exploring' | 'scale'
const STATUS_LABEL: Record<Status, string> = {
  shipped: 'Shipped',
  progress: 'In progress',
  exploring: 'Exploring',
  scale: 'At scale',
}
function statusClass(s: Status) {
  return {
    shipped: 'ape-chip-pos',
    progress: 'ape-chip-strategy',
    exploring: '',
    scale: 'ape-chip-redraw',
  }[s]
}

/* What works today, the v1 system actually running behind this app. */
const shipped = [
  { icon: BoltIcon, title: 'Per-user format memory', body: 'Fair first trials, then confidence-weighted picks choose the response format for each user and each question type, live on every turn.' },
  { icon: ShieldCheckIcon, title: 'Two-axis rewards', body: 'Content vs. format scored separately; only format moves the memory. The politeness firewall keeps “thanks!” from teaching the wrong lesson.' },
  { icon: ArrowTrendingUpIcon, title: 'Session-based learning', body: 'Reactions attach to the exact answer they refer to, with no turn ids to track, using conditional writes that can’t double-apply.' },
  { icon: Squares2X2Icon, title: 'Governed live widgets', body: 'Charts and tables render from a closed component registry, validated before display. No fabricated data, no model-generated HTML.' },
  { icon: SparklesIcon, title: 'Transparent telemetry', body: 'Every answer shows the strategy, intent, and the reward your reaction banked, you can watch it learn.' },
  { icon: ChatBubbleLeftRightIcon, title: 'Public, login-free', body: 'A guest identity per browser keeps personalization working with zero sign-up friction.' },
]

/* The roadmap proper, phased, honest, with status. */
const phases = [
  {
    tag: 'Phase 1',
    status: 'progress' as Status,
    title: 'Production deployment',
    body: 'Move APE onto its target stack: one Lambda (Mangum-wrapped FastAPI) behind API Gateway, with DynamoDB as the store. Every hot-path operation is already a single key lookup or conditional update, DynamoDB’s native shape.',
    items: [
      'DynamoStore + Lambda templates exist and are inert until activated',
      'Reward runs synchronously inline on Lambda (~10 ms), no lost writes on container freeze',
      'Remaining work: port the remaining data-access call sites and the analytics scan-aggregate',
    ],
  },
  {
    tag: 'Phase 2',
    status: 'exploring' as Status,
    title: 'Richer feedback signals',
    body: 'The engine only learns as fast as the signal arrives. Adding high-frequency, unambiguous signals roughly triples the effective feedback rate without adding noise.',
    items: [
      'copy / save and regenerate clicks, frequent UI events the engine can trust',
      'A format-compliance gate: if the LLM didn’t honor the chosen shape, the turn is skipped, not mis-attributed',
      'No confounded signals (dwell time, scroll depth), those stay analytics-only',
    ],
  },
  {
    tag: 'Phase 3',
    status: 'exploring' as Status,
    title: 'Chart formats as first-class arms',
    body: 'Today chart type is the LLM’s call. Once the UI render contract is fixed, “visual vs. table vs. prose” can become a learnable choice, while the specific chart kind stays the model’s job.',
    items: [
      'A “visualization” option the engine can select for data-shaped intents',
      'Lane router already separates chart-redraw requests from text-format requests',
      'Promotion driven by observed data, not guessed in advance',
    ],
  },
  {
    tag: 'Phase 4',
    status: 'exploring' as Status,
    title: 'The transformation layer',
    body: 'A second, stacked learner that picks the teaching strategy (analogy, first-principles, formal definition…) above the format. Validated in shadow mode first, learned globally where data is dense, kept per-user only where it converges.',
    items: [
      'Shadow mode measures signal rate + classifier accuracy at zero user risk',
      'Warm-start from a global pool so new users never start cold',
      'Kill criterion agreed up front, ship only if the data supports it',
    ],
  },
  {
    tag: 'At scale',
    status: 'scale' as Status,
    title: 'Decoupled reward pipeline',
    body: 'Only when rewards become heavy or must never be lost: move REWARD onto SQS with a second Lambda and a dead-letter queue. The switch is a single environment flag, not a rewrite.',
    items: [
      'Triggers: heavy reward compute, audit-grade durability, or spiky feedback volume',
      'No SQS / SNS / graph database before they earn their place',
    ],
  },
]
</script>

<template>
  <div class="w-full px-4 lg:px-6 pb-16">
    <div class="max-w-6xl mx-auto space-y-10 py-6 lg:py-8 page-content">

      <!-- header -->
      <header class="relative overflow-hidden rounded-3xl border bg-card/60 glass-panel scene-3d">
        <div class="orb orb-cyan orb-float-a h-64 w-64 -top-16 -left-10" />
        <div class="orb orb-violet orb-float-b h-72 w-72 -bottom-20 right-0" />
        <div class="relative p-7 lg:p-10 space-y-4 rise-in">
          <div class="inline-flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-muted-foreground rounded-full border bg-background/70 px-3 py-1.5">
            <BoltIcon class="h-3.5 w-3.5 text-primary" />
            APE · Adaptive Personalisation Engine
          </div>
          <h1 class="text-3xl lg:text-4xl font-semibold tracking-tight text-balance">
            Roadmap:
            <span class="text-foreground">what’s built, what’s next</span>
          </h1>
          <p class="text-sm text-muted-foreground leading-relaxed max-w-2xl">
            A working format engine ships today. Everything ahead is staged so each step is
            validated before the next, learn where the data can support it, and never add
            infrastructure before it earns its place.
          </p>
        </div>
      </header>

      <!-- now shipping -->
      <section class="space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-semibold tracking-tight">Now shipping</h2>
          <span class="ape-chip ape-chip-pos">Live in this app</span>
        </div>
        <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div
            v-for="(f, i) in shipped"
            :key="f.title"
            class="rise-in rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover space-y-2.5"
            :style="{ '--stagger': (i % 3) * 0.06 + 's' }"
          >
            <div class="h-9 w-9 rounded-lg bg-primary/12 border border-primary/30 flex items-center justify-center">
              <component :is="f.icon" class="h-4.5 w-4.5 text-primary" />
            </div>
            <h3 class="font-semibold text-sm">{{ f.title }}</h3>
            <p class="text-xs text-muted-foreground leading-relaxed">{{ f.body }}</p>
          </div>
        </div>
      </section>

      <!-- phased roadmap -->
      <section class="space-y-4">
        <h2 class="text-xl font-semibold tracking-tight">The path forward</h2>
        <div class="relative space-y-3">
          <!-- timeline rail -->
          <div class="absolute left-[19px] top-3 bottom-3 w-px bg-gradient-to-b from-teal-400/40 via-border to-teal-400/25 hidden sm:block" />
          <div
            v-for="(ph, i) in phases"
            :key="ph.tag"
            class="rise-in relative rounded-2xl border bg-card/70 glass-panel p-5 sm:pl-14 tilt-3d tilt-hover"
            :style="{ '--stagger': i * 0.06 + 's' }"
          >
            <!-- timeline node -->
            <div class="absolute left-2.5 top-5 h-7 w-7 rounded-full border-2 border-primary/40 bg-card hidden sm:flex items-center justify-center text-[10px] font-bold text-primary">
              {{ i + 1 }}
            </div>
            <div class="flex flex-wrap items-center gap-2 mb-2">
              <span class="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">{{ ph.tag }}</span>
              <span class="ape-chip" :class="statusClass(ph.status)">{{ STATUS_LABEL[ph.status] }}</span>
            </div>
            <h3 class="font-semibold">{{ ph.title }}</h3>
            <p class="text-sm text-muted-foreground leading-relaxed mt-1.5">{{ ph.body }}</p>
            <ul class="mt-3 space-y-1.5">
              <li v-for="it in ph.items" :key="it" class="flex gap-2 text-xs text-muted-foreground">
                <span class="text-primary mt-0.5">▸</span><span class="leading-relaxed">{{ it }}</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <!-- honesty note + CTA -->
      <section class="rounded-2xl border bg-card/70 glass-panel p-6 space-y-3">
        <div class="flex items-center gap-2">
          <CpuChipIcon class="h-4 w-4 text-primary" />
          <h2 class="text-sm font-semibold">A note on what’s real</h2>
        </div>
        <p class="text-xs text-muted-foreground leading-relaxed">
          The format engine works today and is measured. The phases beyond are deliberately gated:
          the transformation layer ships only if shadow-mode data shows the feedback signal is strong
          enough and the classifier can cleanly split a “teaching” complaint from a “shape” complaint.
          The worst case is still a good product, every user gets the population-best format and
          transformation; per-user depth is the upside, never the foundation.
        </p>
      </section>

      <div class="flex flex-wrap items-center gap-3">
        <Button to="/app/chat" class="h-11 px-6 text-sm gap-2">
          <ChatBubbleLeftRightIcon class="h-4 w-4" />
          Try it now
        </Button>
        <Button to="/app/about" variant="outline" class="h-11 px-6 text-sm gap-2">
          <SparklesIcon class="h-4 w-4" />
          How it works
        </Button>
      </div>

    </div>
  </div>
</template>
