<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import Button from '@/components/ui/Button.vue'
import VizChart from '@/components/viz/VizChart.vue'
import FormatMorph from '@/components/viz/FormatMorph.vue'
import CountUp from '@/components/viz/CountUp.vue'
import {
  BoltIcon,
  ChatBubbleLeftRightIcon,
  SparklesIcon,
  ShieldCheckIcon,
  CpuChipIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
} from '@/components/icons'

/* Mouse-follow 3D tilt for the hero visual (reduced-motion aware). */
const heroScene = ref<HTMLDivElement | null>(null)
const tiltStyle = ref<Record<string, string>>({})
let reduceMotion = false

function onHeroMove(e: MouseEvent) {
  if (reduceMotion || !heroScene.value) return
  const r = heroScene.value.getBoundingClientRect()
  const px = (e.clientX - r.left) / r.width - 0.5
  const py = (e.clientY - r.top) / r.height - 0.5
  tiltStyle.value = {
    transform: `rotateX(${(-py * 9).toFixed(2)}deg) rotateY(${(px * 13).toFixed(2)}deg)`,
  }
}
function onHeroLeave() {
  tiltStyle.value = { transform: 'rotateX(0deg) rotateY(0deg)' }
}
onMounted(() => {
  reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
})

// Standalone /about gets its own header (back + brand + CTA). At /app/about the
// AppShell already provides navigation, so the header is hidden there.
const route = useRoute()
const router = useRouter()
const isStandalone = computed(() => !route.path.startsWith('/app'))
function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/')
}

const stats = [
  { end: 3, prefix: '~', suffix: ' ms', label: 'format decision', sub: '100–1000× faster than the LLM call it precedes' },
  { end: 18, label: 'response formats', sub: 'tables, summaries, checklists, one-liners…' },
  { end: 9, label: 'reaction signals', sub: 'a closed set, nothing ambiguous sneaks in' },
  { end: 6, label: 'question intents', sub: 'each gets its own per-user scoreboard' },
]

const signals = [
  { label: '“this layout is perfect”', score: '+2', tone: 'pos' },
  { label: 'thumbs up', score: '+1', tone: 'pos' },
  { label: 'thumbs down', score: '−1', tone: 'neg' },
  { label: '“make it a table instead”', score: '−2', tone: 'neg' },
  { label: '“thanks!” / a follow-up', score: '0', tone: 'zero' },
]

const steps = [
  { n: '01', title: 'Classify', body: 'A fast model reads the message: what kind of question is it, and how did the user react to the last answer?' },
  { n: '02', title: 'Select', body: 'APE checks this user’s scoreboard for that intent and picks the format, explore early, exploit what works.' },
  { n: '03', title: 'Generate', body: 'The LLM writes the answer in that shape, plus a live data widget when the numbers deserve one.' },
  { n: '04', title: 'Learn', body: 'Thumbs and natural reactions become rewards on the exact answer they refer to. Next pick is sharper.' },
]
</script>

<template>
  <div>

    <!-- Standalone header — back, brand, CTA. Hidden inside the app shell. -->
    <header v-if="isStandalone" class="sticky top-0 z-40 border-b bg-background/80 backdrop-blur-md">
      <div class="max-w-6xl mx-auto flex items-center justify-between gap-3 px-4 lg:px-6 h-14">
        <div class="flex items-center gap-2 sm:gap-4">
          <button
            type="button"
            @click="goBack"
            class="inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-sm text-foreground/80 hover:bg-muted/60 transition cursor-pointer"
          >
            <svg viewBox="0 0 20 20" fill="none" class="h-4 w-4"><path d="M12.5 15l-5-5 5-5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" /></svg>
            Back
          </button>
          <RouterLink to="/" class="flex items-center gap-2" aria-label="APE home">
            <svg viewBox="0 0 24 24" class="h-7 w-7">
              <rect width="24" height="24" rx="6" fill="#131316" />
              <rect x="6" y="7" width="12" height="2.2" rx="1.1" fill="#eceef6" opacity="0.85" />
              <rect x="6" y="11" width="12" height="2.2" rx="1.1" fill="#ff060a" />
              <rect x="6" y="15" width="9" height="2.2" rx="1.1" fill="#eceef6" opacity="0.85" />
            </svg>
            <span class="text-sm font-semibold tracking-tight">APE</span>
          </RouterLink>
        </div>
        <div class="flex items-center gap-1.5">
          <RouterLink to="/" class="hidden sm:inline-flex text-sm text-muted-foreground hover:text-foreground px-3 py-1.5 transition">Home</RouterLink>
          <Button to="/app/chat" class="h-9 px-4 text-sm">Get started</Button>
        </div>
      </div>
    </header>

    <div class="w-full px-4 lg:px-6 pb-20">

    <!-- ================= HERO ================= -->
    <section
      ref="heroScene"
      class="relative overflow-hidden rounded-3xl border bg-card/60 glass-panel mt-4 scene-3d bg-dotgrid max-w-6xl mx-auto"
      @mousemove="onHeroMove"
      @mouseleave="onHeroLeave"
    >
      <div class="orb orb-cyan orb-float-a h-72 w-72 -top-16 -left-16" />
      <div class="orb orb-violet orb-float-b h-80 w-80 -bottom-24 right-10" />

      <div class="relative grid lg:grid-cols-[1.05fr_0.95fr] gap-8 items-center p-8 lg:p-14">
        <div class="space-y-6 rise-in">
          <div class="inline-flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-muted-foreground rounded-full border bg-background/70 px-3 py-1.5">
            <BoltIcon class="h-3.5 w-3.5 text-primary" />
            APE · Adaptive Personalisation Engine
          </div>
          <h1 class="text-5xl lg:text-6xl font-semibold tracking-[-0.035em] leading-[1.02] text-balance">
            Right answer.
            <span class="text-foreground">Right shape.</span>
            Every time.
          </h1>
          <p class="text-base lg:text-lg text-muted-foreground leading-relaxed max-w-xl">
            The same correct answer can land as a wall of text or a clean table, and the wrong
            shape makes a right answer hard to use. APE learns which format works for
            <em>you</em>, per kind of question, from nothing but your natural reactions.
          </p>
          <div class="flex flex-wrap items-center gap-3">
            <Button to="/app/chat" class="btn-shine h-11 px-6 text-sm gap-2">
              <ChatBubbleLeftRightIcon class="h-4 w-4" />
              Open the chat
            </Button>
            <a href="#two-jobs">
              <Button variant="outline" class="h-11 px-6 text-sm gap-2">
                <SparklesIcon class="h-4 w-4" />
                How it works
              </Button>
            </a>
          </div>
          <p class="text-xs text-muted-foreground">
            The LLM owns the content. APE owns the format. Neither ever touches the other’s job.
          </p>
        </div>

        <!-- live morph demo in 3D -->
        <div class="relative h-[340px] hidden lg:block select-none" aria-hidden="true">
          <div class="glow-ring" />
          <div class="absolute inset-0 tilt-3d flex items-center justify-center" :style="tiltStyle">
            <div class="w-80 hero-card rounded-2xl">
              <FormatMorph />
            </div>
            <div class="chip-float absolute top-6 left-4" style="--chip-rot: -6deg">
              <div class="ape-chip ape-chip-pos">+1.0 reward</div>
            </div>
            <div class="chip-float absolute bottom-8 right-2" style="--chip-rot: 5deg; animation-delay: -3s">
              <div class="ape-chip ape-chip-strategy"><BoltIcon class="h-3 w-3" /> learned · memory</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= STATS ================= -->
    <section v-reveal class="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-6 max-w-6xl mx-auto">
      <div
        v-for="s in stats"
        :key="s.label"
        class="rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover"
      >
        <div class="stat-num text-3xl"><CountUp :end="s.end" :prefix="s.prefix" :suffix="s.suffix" /></div>
        <div class="text-sm font-medium mt-1">{{ s.label }}</div>
        <div class="text-xs text-muted-foreground mt-1 leading-relaxed">{{ s.sub }}</div>
      </div>
    </section>

    <!-- ================= TWO JOBS ================= -->
    <section id="two-jobs" class="mt-20 space-y-6 scroll-mt-16 max-w-6xl mx-auto">
      <div v-reveal class="text-center space-y-3">
        <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em]">Two jobs, one call</h2>
        <p class="text-sm text-muted-foreground max-w-2xl mx-auto">
          Every message triggers both, and neither ever slows your answer down.
        </p>
      </div>
      <div v-reveal="100" class="grid md:grid-cols-2 gap-4">
        <!-- SELECT with live visual -->
        <div class="rounded-2xl border bg-card/70 glass-panel p-6 tilt-3d tilt-hover space-y-4">
          <div class="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-primary">
            <span class="h-7 w-7 rounded-lg bg-primary/12 border border-primary/30 inline-flex items-center justify-center">S</span>
            Select
          </div>
          <h3 class="font-semibold">Pick the format, before the answer is written</h3>
          <p class="text-sm text-muted-foreground leading-relaxed">
            “Which plan should I choose?” is a comparison, so APE hands the LLM a comparison-table
            instruction. New users get a fair round-robin tour of the formats; after that, the best
            scorer leads.
          </p>
          <div class="pt-1"><FormatMorph /></div>
        </div>
        <!-- REWARD with reaction visual -->
        <div class="rounded-2xl border bg-card/70 glass-panel p-6 tilt-3d tilt-hover space-y-4">
          <div class="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-red-300">
            <span class="h-7 w-7 rounded-lg bg-red-500/12 border border-red-500/30 inline-flex items-center justify-center">R</span>
            Reward
          </div>
          <h3 class="font-semibold">Learn from the reaction, on the next turn</h3>
          <p class="text-sm text-muted-foreground leading-relaxed">
            You reply “can you make it shorter?”, a format complaint. The table’s score drops for
            you on comparisons, and a tight summary leads next time. No surveys: your natural
            reactions are the training data.
          </p>
          <!-- reaction → reward → next pick flow -->
          <div class="rounded-2xl border bg-card p-4 space-y-3">
            <div class="flex items-center gap-2 text-xs">
              <span class="text-[10px] text-muted-foreground">You</span>
              <span class="rounded-lg border bg-background/60 px-2.5 py-1.5">can you make it shorter?</span>
            </div>
            <div class="flex items-center gap-2 pl-6">
              <span class="ape-chip ape-chip-neg">−2.0 reward</span>
              <span class="text-muted-foreground text-xs">→</span>
              <span class="ape-chip ape-chip-strategy"><BoltIcon class="h-3 w-3" /> next: bullet summary</span>
            </div>
            <div class="flex items-center gap-2 pl-6">
              <span class="ape-chip"><HandThumbUpIcon class="h-3 w-3" /> +1</span>
              <span class="ape-chip"><HandThumbDownIcon class="h-3 w-3" /> −1</span>
              <span class="text-[10px] text-muted-foreground">thumbs are weaker evidence than words</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= THE LIFE OF A TURN ================= -->
    <section class="mt-20 space-y-6 max-w-6xl mx-auto">
      <div v-reveal class="text-center space-y-3">
        <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em]">The life of a turn</h2>
        <p class="text-sm text-muted-foreground max-w-2xl mx-auto">
          Four steps, with overhead measured in milliseconds.
        </p>
      </div>
      <div v-reveal="100" class="relative">
        <div class="flow-line hidden lg:block" aria-hidden="true" />
        <div class="relative grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div
            v-for="st in steps"
            :key="st.n"
            class="rounded-2xl border bg-card/85 glass-panel p-5 tilt-3d tilt-hover"
          >
            <div class="text-[28px] font-bold text-foreground">{{ st.n }}</div>
            <div class="font-semibold mt-1">{{ st.title }}</div>
            <p class="text-xs text-muted-foreground mt-1.5 leading-relaxed">{{ st.body }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= SCORING + LEARNING (full-bleed band) ================= -->
    <section class="mt-20 -mx-4 lg:-mx-6 bg-dotgrid relative overflow-hidden">
      <div class="orb orb-cyan orb-float-a h-72 w-72 -left-20 top-10" />
      <div class="max-w-6xl mx-auto px-4 lg:px-6 py-14 grid lg:grid-cols-2 gap-4 items-stretch">
      <div v-reveal class="rounded-2xl border bg-card/70 glass-panel p-6 space-y-4">
        <h2 class="text-2xl lg:text-3xl font-semibold tracking-tight">Scoring that can’t be flattered</h2>
        <p class="text-sm text-muted-foreground leading-relaxed">
          Every reaction is scored on two separate axes, was the <strong>answer</strong> good, and was
          the <strong>shape</strong> good. Only the shape moves the format engine. A polite “thanks!”
          is never mistaken for “I loved the layout”, the politeness firewall.
        </p>
        <div class="space-y-2">
          <div
            v-for="sig in signals"
            :key="sig.label"
            class="flex items-center justify-between rounded-xl border bg-background/50 px-3 py-2"
          >
            <span class="text-sm">{{ sig.label }}</span>
            <span
              class="ape-chip"
              :class="sig.tone === 'pos' ? 'ape-chip-pos' : sig.tone === 'neg' ? 'ape-chip-neg' : ''"
            >{{ sig.score }} format</span>
          </div>
        </div>
      </div>

      <div v-reveal="100" class="rounded-2xl border bg-card/70 glass-panel p-6 space-y-4">
        <h2 class="text-2xl lg:text-3xl font-semibold tracking-tight">Learns like a scientist</h2>
        <p class="text-sm text-muted-foreground leading-relaxed">
          It learns the way a careful scientist would: lean on the formats that earned the best reactions,
          keep a deliberate sliver of curiosity, never get stuck on a lucky early winner.
        </p>
        <div class="rounded-xl border bg-background/60 p-4 font-mono text-[13px] text-muted-foreground">
          next pick = proven results + a measured dose of curiosity
          <div class="mt-1 text-[11px]">
            <span class="text-primary">lean on what works</span> +
            <span class="text-red-300"> keep testing what might</span>
          </div>
        </div>
        <div class="h-28 text-red-300"><VizChart kind="bars" /></div>
        <ul class="space-y-2 text-sm text-muted-foreground">
          <li class="flex gap-2"><span class="text-primary">•</span> Decisions computed live, nothing cached, nothing stale.</li>
          <li class="flex gap-2"><span class="text-primary">•</span> Per user <em>and</em> per question type, comparisons and definitions learn separately.</li>
          <li class="flex gap-2"><span class="text-primary">•</span> Chart redraws (“pie chart instead”) never pollute the text scoreboard.</li>
        </ul>
      </div>
      </div>
    </section>

    <!-- ================= GOVERNED VISUALS ================= -->
    <section v-reveal class="mt-20 rounded-3xl border bg-card/70 glass-panel p-6 lg:p-10 overflow-hidden relative max-w-6xl mx-auto">
      <div class="orb orb-violet orb-float-b h-64 w-64 -right-20 -top-16" />
      <div class="relative grid lg:grid-cols-[1fr_0.9fr] gap-8 items-center">
        <div class="space-y-4">
          <h2 class="text-3xl lg:text-4xl font-semibold tracking-[-0.03em]">Governed visuals, not generated HTML</h2>
          <p class="text-sm text-muted-foreground leading-relaxed">
            When an answer carries real data, the model fills a chart or KPI widget, but only from the
            app’s own component registry, validated before it renders. No fabricated numbers, no raw
            model HTML, no iframes. One component definition, many data fills, zero model-generated UI.
          </p>
          <div class="flex flex-wrap gap-2">
            <span v-for="k in ['bar', 'line', 'pie', 'treemap', 'heatmap', 'sankey', 'radar', 'gauge', '+25 more']" :key="k" class="ape-chip">{{ k }}</span>
          </div>
          <div class="flex flex-wrap items-center gap-x-6 gap-y-2 pt-1 text-[11px] text-muted-foreground">
            <span class="inline-flex items-center gap-1.5"><ShieldCheckIcon class="h-3.5 w-3.5 text-primary" /> registry-validated</span>
            <span class="inline-flex items-center gap-1.5"><ShieldCheckIcon class="h-3.5 w-3.5 text-primary" /> real data only</span>
            <span class="inline-flex items-center gap-1.5"><CpuChipIcon class="h-3.5 w-3.5 text-primary" /> renders as your components</span>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="rounded-2xl border bg-card/80 p-4 viz-card"><div class="h-24 text-red-300"><VizChart kind="bars" /></div></div>
          <div class="rounded-2xl border bg-card/80 p-4 viz-card"><div class="h-24 text-primary flex items-center justify-center"><VizChart kind="donut" /></div></div>
          <div class="rounded-2xl border bg-card/80 p-4 viz-card"><div class="h-24 text-red-400"><VizChart kind="area" /></div></div>
          <div class="rounded-2xl border bg-card/80 p-4 viz-card"><div class="h-24 text-primary"><VizChart kind="iso" /></div></div>
        </div>
      </div>
    </section>

    <!-- ================= CTA ================= -->
    <section v-reveal class="mt-20 relative overflow-hidden rounded-3xl border glass-panel p-10 lg:p-14 text-center max-w-6xl mx-auto">
      <div class="orb orb-cyan orb-float-b h-64 w-64 -top-20 left-1/4" />
      <div class="orb orb-violet orb-float-a h-64 w-64 -bottom-24 right-1/4" />
      <div class="relative space-y-4">
        <h2 class="text-3xl lg:text-4xl font-semibold tracking-[-0.03em]">Ask it something. Then tell it what you think.</h2>
        <p class="text-sm text-muted-foreground max-w-xl mx-auto">
          Every thumbs-up, every “make it shorter”, every redraw teaches it your preference,
          and you can watch the learning happen, right on each answer.
        </p>
        <Button to="/app/chat" class="btn-shine h-11 px-8 text-sm gap-2">
          <ChatBubbleLeftRightIcon class="h-4 w-4" />
          Start chatting
        </Button>
      </div>
    </section>

    </div>
  </div>
</template>
