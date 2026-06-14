<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { isAuthenticated } from '@/lib/auth'
import AccountMenu from '@/components/AccountMenu.vue'
import Button from '@/components/ui/Button.vue'
import VizChart from '@/components/viz/VizChart.vue'
import TechGlyph from '@/components/viz/TechGlyph.vue'
import CountUp from '@/components/viz/CountUp.vue'
import FormatMorph from '@/components/viz/FormatMorph.vue'
import NeuralBrain from '@/components/viz/NeuralBrain.vue'
import ArchFlow from '@/components/viz/ArchFlow.vue'
import ApePlayground from '@/components/viz/ApePlayground.vue'
import AgentTrace from '@/components/viz/AgentTrace.vue'
import InteractiveChart from '@/components/viz/InteractiveChart.vue'
import { HandThumbUpIcon, HandThumbDownIcon } from '@/components/icons'
import {
  ChatBubbleLeftRightIcon,
  SparklesIcon,
  ShieldCheckIcon,
  CpuChipIcon,
  ArrowTrendingUpIcon,
  CursorArrowRaysIcon,
  Squares2X2Icon,
  InformationCircleIcon,
} from '@/components/icons'

/* Hero is intentionally calm now — no cursor parallax/spotlight. */

/* Top-nav anchors, drives both the nav markup and the scrollspy. */
// In PAGE ORDER: the scrollspy takes the last section whose top has passed
// the nav line, so this list must match the DOM sequence.
const navAnchors = [
  { id: 'home', label: 'Home' },
  { id: 'solves', label: 'Why APE' },
  { id: 'playground', label: 'Playground' },
  { id: 'brain', label: 'Personalisation' },
  { id: 'features', label: 'Features' },
  { id: 'loop', label: 'How it learns' },
]
const activeSection = ref('')

/* Scroll progress hairline + scrollspy (one rAF-throttled handler). */
const scrollProgress = ref(0)
let progressRaf = 0
function onScroll() {
  if (progressRaf) return
  progressRaf = requestAnimationFrame(() => {
    progressRaf = 0
    const max = document.documentElement.scrollHeight - window.innerHeight
    scrollProgress.value = max > 0 ? Math.min(1, window.scrollY / max) : 0
    // scrollspy: the active section is the last one whose top has crossed
    // the nav line (with a small margin so it flips as the heading arrives)
    let current = ''
    for (const a of navAnchors) {
      const el = document.getElementById(a.id)
      if (el && el.getBoundingClientRect().top <= 140) current = a.id
    }
    activeSection.value = current
  })
}

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
})
onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
  if (progressRaf) cancelAnimationFrame(progressRaf)
})

const formats = [
  'comparison table', 'bullet summary', 'one liner', 'decision card', 'numbered steps',
  'checklist', 'pros & cons', 'short paragraph', 'phased workflow', 'definition + example',
  'three-section review', 'bullet contrast', 'analogy explainer', 'statement + actions',
]

const features = [
  {
    icon: SparklesIcon,
    title: 'Adapts the shape, not the facts',
    body: 'The model writes the content; the engine decides whether you see a table, a summary, a checklist, or one tight sentence, per question type, per person.',
  },
  {
    icon: ArrowTrendingUpIcon,
    title: 'Learns from natural reactions',
    body: 'A thumbs-up, a “make it shorter”, a follow-up question, each becomes a precise reward on the exact answer it refers to. No surveys, no settings.',
  },
  {
    icon: ShieldCheckIcon,
    title: 'Can’t be flattered',
    body: 'Reactions are scored on two axes, answer vs. shape. A polite “thanks!” never teaches the engine the wrong lesson. We call it the politeness firewall.',
  },
  {
    icon: Squares2X2Icon,
    title: 'Governed live visuals',
    body: 'Data answers come with real charts, filled from a closed component registry and validated before render. No fabricated numbers, no model-generated HTML.',
  },
  {
    icon: CpuChipIcon,
    title: 'Milliseconds, not seconds',
    body: 'The format decision costs ~3 ms, a rounding error next to the model call. Learning runs alongside the next request, so nothing ever waits.',
  },
  {
    icon: CursorArrowRaysIcon,
    title: 'Transparent, on every answer',
    body: 'Each reply shows what was picked, why, and what reward your reaction banked. You can literally watch it learn your preferences.',
  },
]

const loop = [
  { n: '01', title: 'Classify', body: 'What kind of question is this, and how did you react to the last answer?' },
  { n: '02', title: 'Select', body: 'Your scoreboard for that intent picks the format: explore early, exploit what works.' },
  { n: '03', title: 'Generate', body: 'The model writes the answer in that shape, plus a live widget when data deserves one.' },
  { n: '04', title: 'Learn', body: 'Your reaction becomes a reward on that exact answer. The next pick is sharper.' },
]

/* Illustrative per-domain preference maps, what APE's scoreboards converge
 * to for two example users. Same engine, different domain, different brain. */
const domains = [
  {
    name: 'Finance',
    user: 'a retail investor',
    insight: 'Scans numbers fast. Hates prose for anything quantitative.',
    prefs: [
      { intent: 'Comparisons', format: 'side-by-side tables', v: 0.86 },
      { intent: 'Definitions', format: 'one-liners', v: 0.74 },
      { intent: 'Decisions', format: 'pros & cons', v: 0.62 },
    ],
  },
  {
    name: 'Healthcare',
    user: 'a care coordinator',
    insight: 'Follows procedures. Wants steps she can act on, not essays.',
    prefs: [
      { intent: 'Instructions', format: 'checklists', v: 0.91 },
      { intent: 'Explanations', format: 'numbered steps', v: 0.78 },
      { intent: 'Comparisons', format: 'bullet contrast', v: 0.58 },
    ],
  },
]
const moreDomains = ['Legal', 'Insurance', 'Retail', 'Education', 'Customer support', 'HR', 'Travel', 'Energy']

/* Cognitive facets, the per-user portrait goes deeper than format counts:
 * one confidence-scored cell per kind of thinking. Illustrative examples. */
const facets = [
  {
    name: 'Rebalancing decisions',
    domain: 'Finance',
    score: 88,
    tier: 'High confidence',
    n: 14,
    lead: 'scenario narrative',
    mu: 0.85,
    insight: 'Responds to consequence-framing, abstract risk tables lose them.',
  },
  {
    name: 'Plan selection',
    domain: 'Healthcare',
    score: 79,
    tier: 'Moderate',
    n: 11,
    lead: 'elimination matrix',
    mu: 0.8,
    insight: 'Narrows the field before comparing, reduce first, then decide.',
  },
  {
    name: 'Volatility response',
    domain: 'Finance',
    score: 72,
    tier: 'Moderate',
    n: 8,
    lead: 'historical precedent',
    mu: 0.75,
    insight: 'Under stress, anchors on past outcomes over forward projections.',
  },
]
const RING_C = 2 * Math.PI * 24 // ring circumference for facet score circles

/* Global intelligence, what the whole population teaches the engine.
 * New users warm-start from these priors, then diverge to their own map. */
const trendingTopics = [
  { t: 'Roth vs Traditional', d: '+38%' },
  { t: 'expense ratios', d: '+21%' },
  { t: 'HSA vs FSA', d: '+17%' },
  { t: 'CD ladders', d: '+12%' },
  { t: 'telehealth coverage', d: '+9%' },
  { t: 'index rebalancing', d: '+7%' },
]
const domainShare = [
  { name: 'Finance', v: 38 },
  { name: 'Healthcare', v: 24 },
  { name: 'Customer support', v: 18 },
  { name: 'Education', v: 12 },
  { name: 'Other', v: 8 },
]
const winningStrategies = [
  { q: 'Comparisons', f: 'side-by-side tables', v: 71 },
  { q: 'Definitions', f: 'one-liners', v: 66 },
  { q: 'Instructions', f: 'checklists', v: 64 },
  { q: 'Decisions', f: 'pros & cons', v: 57 },
]

/* Hover-replay for the chart gallery, re-mounting a chart restarts its
 * entrance animation, so every hover is a fresh performance. */
const galleryReplay = ref<Record<string, number>>({})
function rep(k: string) {
  galleryReplay.value[k] = (galleryReplay.value[k] || 0) + 1
}

const brainSteps = [
  { title: 'Understand', body: 'Every reaction (a thumbs, a “make it shorter”, a follow-up) is read as evidence about what worked.' },
  { title: 'Map', body: 'Evidence strengthens pathways: one scoreboard per question type, per person, per domain.' },
  { title: 'Serve', body: 'The strongest pathway answers first. Fewer follow-ups, fewer re-asks, useful on the first try.' },
]

const techStack = [
  { key: 'python', name: 'Python 3.12', role: 'service layer', color: 'text-teal-600 dark:text-teal-300' },
  { key: 'stats', name: 'Adaptive Memory', role: 'expands in real time', color: 'text-teal-600 dark:text-teal-300' },
  { key: 'claude', name: 'Claude', role: 'content generation', color: 'text-primary' },
  { key: 'vue', name: 'Vue 3 · Vite', role: 'reference frontend', color: 'text-emerald-300' },
  { key: 'echarts', name: 'ECharts', role: 'live visualizations', color: 'text-cyan-300' },
  { key: 'lambda', name: 'AWS Lambda', role: 'serverless compute', color: 'text-amber-300' },
  { key: 'dynamodb', name: 'DynamoDB', role: 'production store', color: 'text-sky-300' },
  { key: 'figma', name: 'Figma', role: 'design system', color: 'text-rose-300' },
]

/* "What it solves", concrete operational outcomes, each with a headline stat chip. */
const solves = [
  {
    icon: CpuChipIcon,
    stat: '+0 ms',
    statNote: 'added to p95',
    title: 'Zero drag on your pipeline',
    body: 'The format decision is a ~3 ms lookup before generation, and learning happens off the hot path, rewards ride the next request. Your latency budget doesn’t move.',
  },
  {
    icon: ChatBubbleLeftRightIcon,
    stat: '↓ re-asks',
    statNote: 'per session',
    title: 'Fewer follow-ups',
    body: '“Make it shorter.” “Can I get a table?” Those turns disappear as the map sharpens, the answer lands in the user’s preferred shape on the first try.',
  },
  {
    icon: Squares2X2Icon,
    stat: '↓ tokens',
    statNote: 'right-sized output',
    title: 'Token control, by design',
    body: 'A one-liner where a one-liner wins; a table instead of three paragraphs. Right-sizing every answer cuts output tokens, and the follow-ups you no longer pay for.',
  },
  {
    icon: ShieldCheckIcon,
    stat: 'governed',
    statNote: 'closed catalogs',
    title: 'Acts as a guardrail',
    body: 'Formats and visuals come from closed, governed registries, never invented. A politeness firewall keeps “thanks!” from inflating scores, and APE shapes form only, never facts.',
  },
  {
    icon: CpuChipIcon,
    stat: '0 changes',
    statNote: 'to your stack',
    title: 'Plugs in, changes nothing',
    body: 'One HTTP call between intent and synthesis. Your retriever, your agents, your prompts and your models stay exactly as they are today.',
  },
  {
    icon: ArrowTrendingUpIcon,
    stat: '100%',
    statNote: 'auditable picks',
    title: 'Every decision is auditable',
    body: 'Each pick records whether it explored or exploited, the scores behind it, and the reward that came back. Replayable, explainable, no black box.',
  },
]

/* Tech stack as two counter-scrolling marquee rows. */
const techRowA = techStack.slice(0, 4)
const techRowB = techStack.slice(4)

/* Domains the map adapts to, rendered as a moving strip (same treatment
 * as the tech stack). The point: nothing here is hardcoded; the map keys
 * itself by whatever domain your traffic carries. */
const domainStrip = [
  { name: 'Finance', dot: '#0d9488' },
  { name: 'Healthcare', dot: '#34d399' },
  { name: 'Legal', dot: '#0f766e' },
  { name: 'E-commerce', dot: '#22d3ee' },
  { name: 'Education', dot: '#5eead4' },
  { name: 'Insurance', dot: '#2dd4bf' },
  { name: 'Manufacturing', dot: '#14b8a6' },
  { name: 'Travel', dot: '#fb7185' },
  { name: 'Energy', dot: '#38bdf8' },
  { name: 'Customer support', dot: '#c4b5fd' },
]

/* Side-by-side: generic assistants vs an APE-powered app, same question.
 * The APE card toggles between two learned users to show the same content
 * arriving in two different shapes. */
const comparePersona = ref<'priya' | 'marcus'>('priya')

/* FAQ, the objections a technical buyer actually has. */
const faqs = [
  {
    q: 'Why APE? Why not just prompt the LLM directly?',
    a: 'A prompt is one static guess; APE is a measurement system. “Prefer tables” in a system prompt is the same for every user and every question, but format preference differs per person and per question type, and only shows up in behaviour. You could stuff reaction history into the context instead, but then you pay for those tokens on every call, the model can be swayed by flattery, and an LLM can’t run a principled explore-vs-exploit trade-off, or tell you why it chose. APE keeps real counters per (user, question-type), decides in ~3 ms with zero prompt bloat, and every pick is auditable. The LLM still writes the answer; APE just hands it one short, evidence-backed format directive.',
  },
  {
    q: 'Why won’t OpenAI or Claude just build this in?',
    a: 'They personalise the model’s answer at the platform level, but they can’t personalise it inside your product, with your components, your tables and charts, and the reactions your own app collects. Their memory is generic and locked to their platform; APE is model-agnostic and lives in your stack, so it keeps learning per user even if you switch models tomorrow. The big labs optimise what gets said. How that answer is shaped and shown to each of your users is the layer you own, and the one APE runs.',
  },
  {
    q: 'Does APE add latency to my pipeline?',
    a: 'Effectively none. The format decision is a ~3 ms state lookup made before generation starts, and learning happens off the hot path, rewards from this answer are banked when the next request arrives. Your p95 stays where it is.',
  },
  {
    q: 'Does it ever change what the model says?',
    a: 'No. It decides the shape of the answer (table, bullets, one-liner, steps), never the facts in it. The LLM owns the content; APE owns the format. A politeness firewall also stops “thanks!” style pleasantries from inflating any format’s score.',
  },
  {
    q: 'What happens if the engine goes down?',
    a: 'Nothing visible. The client gives APE a strict 2.5-second budget; on any failure it serves a neutral format and enters a 30-second cooldown so no further requests pay the timeout. Chat keeps working, and learning resumes when the engine returns.',
  },
  {
    q: 'I asked for a pie chart instead of a bar chart, does that hurt my text-format scores?',
    a: 'No, and this is deliberate. A classifier routes pure chart-kind requests down a separate “widget redraw” lane that skips the engine entirely: no turn is recorded and no format signal is emitted, because “pie, not bar” is a preference about the visual, not the prose. Your queued reactions stay pointed at the answer that actually produced the text.',
  },
  {
    q: 'What does it store about my users?',
    a: 'Per-user format scoreboards keyed by hashed identifiers: which formats were tried for which question types, how often, and how well they landed. Turn records carry the intent, the chosen format, and the signals received. It learns from reactions, not from harvesting message content.',
  },
  {
    q: 'How do I integrate it?',
    a: 'One HTTP call between your intent step and your synthesiser: send the user, session, intent, and any reaction signals; get back a format directive your generator follows. No SDK, no pipeline rewrite, any language, and it works the same for RAG stacks, agent frameworks, and chart applications.',
  },
]
const openFaq = ref<number | null>(0)
function toggleFaq(i: number) {
  openFaq.value = openFaq.value === i ? null : i
}

/* Footer engine-status pill, one health probe on mount. */
const API_BASE = import.meta.env.VITE_API_BASE_URL || ((typeof location !== 'undefined' && /^(localhost|127.0.0.1)$/.test(location.hostname)) ? 'http://localhost:5051' : '')
const apiUp = ref<boolean | null>(null)
// Drives the nav + hero CTAs: signed-in users see "Open the app", everyone
// else sees Sign in / Get started.
const loggedIn = ref(isAuthenticated())

/* Live counters for the hero eyebrow + ticker strip — real engine numbers. */
const heroStats = ref<null | {
  total_turns: number; total_users: number; total_strategies: number; total_topics: number
}>(null)

onMounted(async () => {
  try {
    const r = await fetch(`${API_BASE}/api/healthz`)
    apiUp.value = r.ok
  } catch {
    apiUp.value = false
  }
  try {
    const s = await fetch(`${API_BASE}/api/playground/stats`)
    const j = await s.json()
    if (j && j.ok) heroStats.value = j
  } catch { /* eyebrow stays plain, ticker stays hidden */ }
})

const integrations = [
  { icon: CpuChipIcon, title: 'Any RAG pipeline', body: 'Keep your retriever and LLM exactly as they are. APE shapes the answer they produce, it never touches retrieval or content.' },
  { icon: SparklesIcon, title: 'Any agentic framework', body: 'Wrap any agent’s final response. One call decides how that response is presented, with zero changes to your agent graph.' },
  { icon: Squares2X2Icon, title: 'Any chart or UI app', body: 'APE returns a format directive your renderer already understands, markdown, your components, or a chart spec.' },
  { icon: CursorArrowRaysIcon, title: 'Any language', body: 'A single HTTP endpoint. No SDK, no lock-in, no change to your generation stack. Drop it in, call it, done.' },
]
</script>

<template>
  <div class="min-h-screen text-foreground relative">

    <!-- Skip link, first tab stop for keyboard users -->
    <a
      href="#content"
      class="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[100] focus:rounded-lg focus:border focus:bg-card focus:px-4 focus:py-2 focus:text-sm focus:shadow-lg"
    >
      Skip to content
    </a>

    <!-- Scroll progress hairline -->
    <div class="scroll-progress" :style="{ width: scrollProgress * 100 + '%' }" aria-hidden="true" />

    <!-- ================= NAV ================= -->
    <header class="sticky top-0 z-50 glass-panel border-b/70">
      <div class="max-w-6xl mx-auto px-4 lg:px-6 h-[52px] flex items-center justify-between gap-4">
        <RouterLink to="/" class="flex items-center gap-2.5 min-w-0">
          <svg viewBox="0 0 100 100" class="h-7 w-7" aria-hidden="true">
            <rect x="2" y="2" width="96" height="96" rx="27" fill="#15140d" />
            <rect x="26" y="31" width="48" height="9" rx="4" fill="#f4f4ec" />
            <rect x="26" y="46" width="48" height="9" rx="4" fill="#14b8a6" />
            <rect x="26" y="61" width="32" height="9" rx="4" fill="#6b6b5e" />
          </svg>
          <span class="font-semibold text-[15px] tracking-tight">APE</span>
        </RouterLink>
        <nav class="hidden md:flex items-center gap-0.5 text-[13px]">
          <a
            v-for="a in navAnchors"
            :key="a.id"
            :href="'#' + a.id"
            class="px-3 py-1.5 rounded-md transition-colors"
            :class="activeSection === a.id
              ? 'text-foreground bg-secondary/70 border border-border/60'
              : 'text-muted-foreground hover:text-foreground'"
            :aria-current="activeSection === a.id ? 'true' : undefined"
          >
            {{ a.label }}
          </a>
          <RouterLink to="/about" class="px-3 py-1.5 rounded-md text-muted-foreground hover:text-foreground transition-colors">About</RouterLink>
        </nav>
        <div class="flex items-center gap-1.5">
          <template v-if="loggedIn">
            <Button to="/app/chat" class="h-8 px-3.5 text-[13px] gap-1.5">
              Open the app
            </Button>
            <AccountMenu />
          </template>
          <template v-else>
            <RouterLink to="/login" class="hidden sm:inline-flex items-center whitespace-nowrap px-3 py-1.5 rounded-md text-[13px] text-muted-foreground hover:text-foreground transition-colors">
              Sign in
            </RouterLink>
            <Button to="/login?mode=register" class="h-8 px-3.5 text-[13px] gap-1.5">
              Get started
            </Button>
          </template>
        </div>
      </div>
    </header>

    <main id="content">
    <!-- ================= HERO ================= -->
    <section
      id="home"
      class="relative overflow-hidden bg-dotgrid scroll-mt-16"
    >
      <div class="relative max-w-6xl mx-auto px-4 lg:px-6 pt-16 lg:pt-24 pb-16 grid lg:grid-cols-[1.05fr_0.95fr] gap-10 items-center">
        <!-- copy -->
        <div class="space-y-7">
          <div class="hero-late eyebrow" style="--d: 0.05s">
            the response-format layer
            <span v-if="heroStats && heroStats.total_turns > 0" class="eyebrow-chip"><CountUp :end="heroStats.total_turns" /> learned</span>
            <span v-else class="eyebrow-chip">live</span>
          </div>
          <h1 class="text-4xl sm:text-5xl lg:text-[56px] font-semibold tracking-[-0.03em] leading-[1.08]">
            <span class="hero-word" style="--d: 0.1s">Answers</span>
            <span class="hero-word" style="--d: 0.2s">that</span><br />
            <!-- gradient applied PER word: bg-clip-text can't paint through transformed children -->
            <span class="hero-word" style="--d: 0.32s">take</span>
            <span class="hero-word" style="--d: 0.42s">your</span>
            <span class="hero-word hl-accent" style="--d: 0.52s">shape</span>
          </h1>
          <p class="hero-late text-base lg:text-lg text-muted-foreground leading-relaxed max-w-xl" style="--d: 0.65s">
            One user needs the side-by-side table; another wants the two-line verdict. APE learns
            which one each person is and answers in that shape. It is the response-format layer that
            sits on top of your memory, RAG, or agents, the one thing they don’t do.
          </p>
          <div class="hero-late flex flex-wrap items-center gap-3" style="--d: 0.8s">
            <Button v-magnet :to="loggedIn ? '/app/chat' : '/login?mode=register'" class="btn-shine h-12 px-7 text-sm gap-2 shadow-md shadow-black/10">
              <ChatBubbleLeftRightIcon class="h-4 w-4" />
              {{ loggedIn ? 'Open the app' : 'Get started, it’s free' }}
            </Button>
            <Button to="/about" variant="outline" class="h-12 px-7 text-sm gap-2">
              <InformationCircleIcon class="h-4 w-4" />
              How it works
            </Button>
          </div>
          <div class="hero-late flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-muted-foreground pt-1" style="--d: 0.95s">
            <span>real-time memory</span>
            <span class="text-muted-foreground/40">·</span>
            <span>~<CountUp :end="3" suffix=" ms" /> decisions</span>
            <span class="text-muted-foreground/40">·</span>
            <span><CountUp :end="18" /> formats</span>
            <span class="text-muted-foreground/40">·</span>
            <span>governed visuals</span>
          </div>
        </div>

        <!-- one clean product visual: the adaptive answer card -->
        <div class="hero-late flex justify-center lg:justify-end" style="--d: 0.55s">
          <div class="relative w-full max-w-sm">
            <div class="rounded-2xl border bg-card glass-panel shadow-xl shadow-black/5 overflow-hidden">
              <FormatMorph />
            </div>
            <div class="core-badge">live memory</div>
          </div>
        </div>
      </div>

      <!-- Ramp-style live ticker — real numbers straight from the engine -->
      <div v-if="heroStats" class="relative border-y bg-card/70">
        <div class="max-w-6xl mx-auto px-4 lg:px-6 py-2.5 flex flex-wrap items-center justify-between gap-x-8 gap-y-2">
          <span class="eyebrow">
            <span class="relative flex h-1.5 w-1.5">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-500 opacity-70" />
              <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-teal-500" />
            </span>
            the engine at work
          </span>
          <span class="eyebrow">turns learned <span class="eyebrow-chip"><CountUp :end="heroStats.total_turns" /></span></span>
          <span class="eyebrow">users mapped <span class="eyebrow-chip"><CountUp :end="heroStats.total_users" /></span></span>
          <span class="eyebrow hidden sm:inline-flex">formats <span class="eyebrow-chip"><CountUp :end="heroStats.total_strategies" /></span></span>
          <span class="eyebrow hidden md:inline-flex">topics tracked <span class="eyebrow-chip"><CountUp :end="heroStats.total_topics" /></span></span>
        </div>
      </div>

      <!-- formats marquee -->
      <div class="relative max-w-6xl mx-auto px-4 lg:px-6 pb-12 pt-10">
        <div class="marquee-mask rounded-2xl border bg-card/50 glass-panel py-3">
          <div class="marquee px-3">
            <span v-for="(f, i) in [...formats, ...formats]" :key="i" class="ape-chip whitespace-nowrap">
              {{ f }}
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= SIDE BY SIDE: SAME QUESTION, THREE ANSWERS ================= -->
    <section id="compare" class="relative max-w-6xl mx-auto px-4 lg:px-6 py-24 scroll-mt-16">
      <div v-reveal class="text-center space-y-3 mb-8">
        <span class="eyebrow">ChatGPT vs Claude vs an APE app</span>
        <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em] text-balance">
          Same question. <span class="text-muted-foreground">Three answers.</span>
        </h2>
        <p class="text-sm text-muted-foreground max-w-2xl mx-auto">
          Great assistants write great prose, for everyone, identically. An APE-powered app answers
          in the shape each user has taught it.
        </p>
      </div>

      <!-- the shared question -->
      <div v-reveal="60" class="max-w-2xl mx-auto mb-8">
        <div class="rounded-2xl border bg-card/70 glass-panel px-5 py-3.5 flex items-start gap-3">
          <span class="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mt-1 shrink-0">You</span>
          <p class="text-sm">Roth IRA or Traditional IRA, which should I pick? I’m 29 and expect my income to rise.</p>
        </div>
      </div>

      <div class="grid lg:grid-cols-3 gap-4 items-stretch">

        <!-- ChatGPT -->
        <div v-reveal="100" class="rise-in rounded-3xl border bg-card/60 glass-panel p-5 flex flex-col">
          <div class="flex items-center gap-2 mb-4">
            <span class="h-2.5 w-2.5 rounded-full bg-emerald-400/80" />
            <span class="text-sm font-medium">ChatGPT</span>
            <span class="ml-auto text-[10px] text-muted-foreground">same for every user</span>
          </div>
          <div class="relative text-[12.5px] text-muted-foreground leading-relaxed space-y-2.5 flex-1">
            <p>Great question! Choosing between a Roth IRA and a Traditional IRA depends on several factors, including your current tax bracket, your expected income trajectory, and your retirement timeline. Let me walk you through the key considerations.</p>
            <p>With a Roth IRA, you contribute after-tax dollars, which means your investments grow tax-free and qualified withdrawals in retirement are not taxed. This tends to favour people who expect to be in a higher tax bracket later…</p>
            <p>A Traditional IRA, on the other hand, may allow you to deduct contributions today, deferring taxes until withdrawal. This can be advantageous if…</p>
            <div class="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-card to-transparent" />
          </div>
          <div class="mt-4 pt-3 border-t border-border/50 text-[11px] text-muted-foreground">
            ~480 words · the same essay, every user, every time
          </div>
        </div>

        <!-- Claude -->
        <div v-reveal="160" class="rise-in rounded-3xl border bg-card/60 glass-panel p-5 flex flex-col">
          <div class="flex items-center gap-2 mb-4">
            <span class="h-2.5 w-2.5 rounded-full bg-orange-400/80" />
            <span class="text-sm font-medium">Claude</span>
            <span class="ml-auto text-[10px] text-muted-foreground">one default style</span>
          </div>
          <div class="relative text-[12.5px] text-muted-foreground leading-relaxed space-y-2.5 flex-1">
            <p>This mostly comes down to when you’d rather pay taxes. Here’s how I’d think about it:</p>
            <p><span class="text-foreground/80 font-medium">Tax timing.</span> A Roth IRA taxes you now and never again; a Traditional IRA defers tax until retirement, which only wins if your rate is lower then…</p>
            <p><span class="text-foreground/80 font-medium">Your situation.</span> At 29 with rising income ahead, today is likely the lowest tax rate you’ll ever pay, which tilts the maths toward…</p>
            <div class="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-card to-transparent" />
          </div>
          <div class="mt-4 pt-3 border-t border-border/50 text-[11px] text-muted-foreground">
            ~390 words · beautifully written, and identical for everyone
          </div>
        </div>

        <!-- APE-powered app -->
        <div v-reveal="220" class="rise-in rounded-3xl border border-teal-400/30 bg-card/70 glass-panel p-5 flex flex-col shadow-lg shadow-teal-500/10">
          <div class="flex items-center gap-2 mb-3">
            <span class="h-2.5 w-2.5 rounded-full bg-primary" />
            <span class="text-sm font-medium">Your app + APE</span>
            <span class="ml-auto text-[10px] text-primary">learned per user</span>
          </div>

          <!-- persona toggle -->
          <div class="grid grid-cols-2 gap-1.5 mb-4">
            <button
              type="button"
              class="flex items-center gap-2 rounded-xl border px-2.5 py-2 text-left transition-all cursor-pointer"
              :class="comparePersona === 'priya' ? 'border-teal-400/40 bg-teal-500/10' : 'hover:border-border opacity-70 hover:opacity-100'"
              :aria-pressed="comparePersona === 'priya'"
              @click="comparePersona = 'priya'"
            >
              <span class="h-7 w-7 shrink-0 rounded-full bg-teal-500/20 border border-teal-400/30 flex items-center justify-center text-[11px] font-semibold text-primary">P</span>
              <span class="min-w-0">
                <span class="block text-[12px] font-medium truncate">Priya</span>
                <span class="block text-[10px] text-muted-foreground truncate">reads the numbers first</span>
              </span>
            </button>
            <button
              type="button"
              class="flex items-center gap-2 rounded-xl border px-2.5 py-2 text-left transition-all cursor-pointer"
              :class="comparePersona === 'marcus' ? 'border-teal-400/40 bg-teal-500/10' : 'hover:border-border opacity-70 hover:opacity-100'"
              :aria-pressed="comparePersona === 'marcus'"
              @click="comparePersona = 'marcus'"
            >
              <span class="h-7 w-7 shrink-0 rounded-full bg-cyan-500/15 border border-cyan-400/25 flex items-center justify-center text-[11px] font-semibold text-cyan-600 dark:text-cyan-300">M</span>
              <span class="min-w-0">
                <span class="block text-[12px] font-medium truncate">Marcus</span>
                <span class="block text-[10px] text-muted-foreground truncate">wants the verdict first</span>
              </span>
            </button>
          </div>

          <!-- Priya: comparison table -->
          <div v-if="comparePersona === 'priya'" :key="'priya'" class="spring-in flex-1 flex flex-col gap-3">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="ape-chip ape-chip-strategy">comparison table</span>
              <span class="ape-chip ape-chip-pos">learned · memory</span>
            </div>
            <div class="rounded-xl border bg-background/50 px-3 text-[11.5px]">
              <div class="grid grid-cols-3 gap-x-3 py-2 font-medium border-b border-border/60">
                <div></div><div class="text-center">Roth</div><div class="text-center">Traditional</div>
              </div>
              <div class="grid grid-cols-3 gap-x-3 py-2 border-b border-border/40">
                <div class="text-muted-foreground">Tax paid</div><div class="text-center">now</div><div class="text-center">at retirement</div>
              </div>
              <div class="grid grid-cols-3 gap-x-3 py-2 border-b border-border/40">
                <div class="text-muted-foreground">Growth</div><div class="text-center text-emerald-500 dark:text-emerald-400">tax-free</div><div class="text-center">tax-deferred</div>
              </div>
              <div class="grid grid-cols-3 gap-x-3 py-2">
                <div class="text-muted-foreground">Wins when</div><div class="text-center text-emerald-500 dark:text-emerald-400">rate rises</div><div class="text-center">rate falls</div>
              </div>
            </div>
            <p class="text-[12.5px] leading-relaxed"><span class="font-medium">Verdict:</span> Roth. At 29 with rising income, today’s rate is likely the lowest you’ll ever pay.</p>
            <div class="mt-auto flex items-center gap-1.5 pt-2">
              <span class="text-[10px] text-muted-foreground mr-0.5">Rate this answer</span>
              <span class="ape-rate-btn is-active-up"><HandThumbUpIcon class="h-3.5 w-3.5" /></span>
              <span class="ape-rate-btn"><HandThumbDownIcon class="h-3.5 w-3.5" /></span>
              <span class="text-[10px] text-muted-foreground">tables keep winning for Priya</span>
            </div>
          </div>

          <!-- Marcus: verdict-first one-liner -->
          <div v-else :key="'marcus'" class="spring-in flex-1 flex flex-col gap-3">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="ape-chip ape-chip-strategy">one liner</span>
              <span class="ape-chip ape-chip-pos">learned · memory</span>
            </div>
            <div class="rounded-xl border bg-background/50 p-4">
              <p class="text-[14px] leading-relaxed font-medium">Take the Roth. You’re trading today’s low tax rate for decades of tax-free growth. Revisit only if your bracket drops.</p>
            </div>
            <p class="text-[11.5px] text-muted-foreground">Full answer in 41 words. The table is one tap away if he ever wants it.</p>
            <div class="mt-auto flex items-center gap-1.5 pt-2">
              <span class="text-[10px] text-muted-foreground mr-0.5">Rate this answer</span>
              <span class="ape-rate-btn is-active-up"><HandThumbUpIcon class="h-3.5 w-3.5" /></span>
              <span class="ape-rate-btn"><HandThumbDownIcon class="h-3.5 w-3.5" /></span>
              <span class="text-[10px] text-muted-foreground">two thumbs-down on essays taught this</span>
            </div>
          </div>

          <div class="mt-4 pt-3 border-t border-border/50 text-[11px] text-muted-foreground">
            Same correct content, in the shape each user taught it
          </div>
        </div>
      </div>

      <p v-reveal="260" class="text-center text-[12px] text-muted-foreground mt-6">
        Toggle the two users above, that switch is the product.
      </p>
    </section>

    <!-- ================= WHAT IT SOLVES ================= -->
    <section id="solves" class="relative max-w-6xl mx-auto px-4 lg:px-6 py-24 scroll-mt-16">
      <div v-reveal class="grid lg:grid-cols-[1fr_2fr] gap-10 lg:gap-16 items-start">
        <div class="lg:sticky lg:top-24 space-y-4">
          <span class="eyebrow">why teams plug it in</span>
          <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em] leading-[1.06] text-balance">
            What it
            <span class="text-muted-foreground">solves.</span>
          </h2>
          <p class="text-sm lg:text-base text-muted-foreground leading-relaxed max-w-sm">
            Personalisation usually costs you something, latency, tokens, control. APE was designed so it costs you none of the three.
          </p>
          <div class="flex flex-wrap gap-2 pt-1">
            <span class="ape-chip">no latency tax</span>
            <span class="ape-chip">no token waste</span>
            <span class="ape-chip">no pipeline rewrites</span>
          </div>
        </div>

        <div class="grid sm:grid-cols-2 gap-3">
          <div
            v-for="(s, i) in solves"
            :key="s.title"
            v-reveal="i * 70"
            class="rise-in group rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover"
          >
            <div class="flex items-center justify-between mb-3.5">
              <div class="h-9 w-9 rounded-xl border border-teal-400/20 bg-teal-500/10 flex items-center justify-center">
                <component :is="s.icon" class="h-4 w-4 text-primary" />
              </div>
              <div class="text-right">
                <div class="text-sm font-semibold tabular-nums text-primary leading-none">{{ s.stat }}</div>
                <div class="text-[10px] text-muted-foreground mt-0.5">{{ s.statNote }}</div>
              </div>
            </div>
            <div class="font-medium text-[15px] mb-1.5">{{ s.title }}</div>
            <p class="text-[13px] text-muted-foreground leading-relaxed">{{ s.body }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= LIVE PLAYGROUND ================= -->
    <section id="playground" class="relative max-w-6xl mx-auto px-4 lg:px-6 py-24 scroll-mt-16">
      <div v-reveal class="text-center space-y-3 mb-10">
        <span class="eyebrow">wired into the live engine</span>
        <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em] text-balance">
          Try the engine. <span class="text-muted-foreground">Live.</span>
        </h2>
        <p class="text-sm text-muted-foreground max-w-2xl mx-auto">
          Pick an intent, ask for a selection, reward it, every click below is a real call into the production
          engine, and the scoreboard is its actual state.
        </p>
      </div>
      <ApePlayground />
    </section>

    <!-- ================= PRODUCT SHOWCASE (editorial rows) ================= -->
    <section id="product" class="relative max-w-6xl mx-auto px-4 lg:px-6 py-24 space-y-24 scroll-mt-16">

      <!-- Row 1: the explained answer -->
      <div v-reveal class="grid lg:grid-cols-2 gap-10 lg:gap-16 items-center">
        <div class="space-y-5">
          <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em] leading-[1.06] text-balance">
            Every answer
            <span class="text-muted-foreground">explains itself.</span>
          </h2>
          <p class="text-sm lg:text-base text-muted-foreground leading-relaxed max-w-md">
            Each reply carries its own reasoning, the format APE picked, whether it was exploring
            or exploiting, the intent it detected, and the reward your last reaction banked.
            Personalisation you can audit, not a black box.
          </p>
          <a href="#loop" class="inline-flex items-center gap-1.5 text-sm text-primary hover:underline underline-offset-4">
            How the learning works <span aria-hidden="true">→</span>
          </a>
        </div>
        <!-- live mockup: real answer card -->
        <div class="scrolly-depth rounded-3xl border bg-card/60 glass-panel p-5 lg:p-7 tilt-3d tilt-hover">
          <div class="rounded-2xl border bg-card p-4 shadow-lg shadow-black/20">
            <div class="text-xs text-muted-foreground mb-1.5 flex items-center gap-1.5 flex-wrap">
              <span class="font-medium text-foreground/80 mr-0.5">Assistant</span>
              <span class="ape-chip ape-chip-strategy">comparison table</span>
              <span class="ape-chip ape-chip-pos">learned · memory</span>
              <span class="ape-chip">Comparison</span>
              <span class="ape-chip ape-chip-pos">+1.0 reward</span>
            </div>
            <div class="text-[13px] leading-relaxed text-foreground/90 mb-2.5">Here's how the two plans compare on what matters:</div>
            <div class="grid grid-cols-3 gap-x-3 gap-y-1.5 text-xs rounded-xl border bg-background/50 p-3">
              <div class="text-muted-foreground"></div><div class="font-medium text-center">HDHP</div><div class="font-medium text-center">Low deductible</div>
              <div class="text-muted-foreground">Premium</div><div class="text-center tabular-nums text-emerald-400">$210/mo</div><div class="text-center tabular-nums">$385/mo</div>
              <div class="text-muted-foreground">Deductible</div><div class="text-center tabular-nums">$3,200</div><div class="text-center tabular-nums text-emerald-400">$750</div>
              <div class="text-muted-foreground">HSA eligible</div><div class="text-center text-emerald-400">Yes</div><div class="text-center">No</div>
            </div>
            <div class="flex items-center gap-1.5 mt-3 pt-2.5 border-t border-border/50">
              <span class="text-[10px] text-muted-foreground mr-0.5">Rate this answer</span>
              <span class="ape-rate-btn is-active-up"><HandThumbUpIcon class="h-3.5 w-3.5" /></span>
              <span class="ape-rate-btn"><HandThumbDownIcon class="h-3.5 w-3.5" /></span>
              <span class="text-[10px] text-muted-foreground">queued, scores this answer with your next message</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Row 2: the live agent trace (flipped) -->
      <div v-reveal class="grid lg:grid-cols-2 gap-10 lg:gap-16 items-center">
        <div class="lg:order-2 space-y-5">
          <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em] leading-[1.06] text-balance">
            Watch it think,
            <span class="text-muted-foreground">live.</span>
          </h2>
          <p class="text-sm lg:text-base text-muted-foreground leading-relaxed max-w-md">
            A real execution trace runs beside every conversation: understand, reward, select,
            generate, render. Each stage lights up as it completes, carrying the actual telemetry
            attached. The same graph your agents would traverse.
          </p>
          <RouterLink to="/app/chat" class="inline-flex items-center gap-1.5 text-sm text-primary hover:underline underline-offset-4">
            See it on your next question <span aria-hidden="true">→</span>
          </RouterLink>
        </div>
        <div class="lg:order-1 scrolly-depth-soft rounded-3xl border bg-card/60 glass-panel p-5 lg:p-7 tilt-3d tilt-hover">
          <div class="max-w-sm mx-auto h-[420px]">
            <AgentTrace
              phase="generate"
              intent="Comparison"
              :signals="['thumbs_up']"
              :reward-applied="1"
              strategy="comparison_table"
              method="learned"
              :has-widget="false"
            />
          </div>
        </div>
      </div>

      <!-- Row 3: living charts -->
      <div v-reveal class="grid lg:grid-cols-2 gap-10 lg:gap-16 items-center">
        <div class="space-y-5">
          <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em] leading-[1.06] text-balance">
            Numbers become
            <span class="text-foreground">living charts.</span>
          </h2>
          <p class="text-sm lg:text-base text-muted-foreground leading-relaxed max-w-md">
            Ask a data question and the answer arrives as an interactive widget, drawn from a
            governed component registry, reshaped on demand, exportable. Never fabricated, never
            raw model HTML.
          </p>
          <a href="#features" class="inline-flex items-center gap-1.5 text-sm text-primary hover:underline underline-offset-4">
            The governed-visuals guarantee <span aria-hidden="true">→</span>
          </a>
        </div>
        <!-- live mockup: chart answer with redraw actions -->
        <div class="scrolly-depth rounded-3xl border bg-card/60 glass-panel p-5 lg:p-7 tilt-3d tilt-hover viz-card">
          <div class="rounded-2xl border bg-card p-4 shadow-lg shadow-black/20">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-medium">Quarterly deliveries by model</span>
              <span class="ape-chip">export anytime</span>
            </div>
            <div class="h-36 text-primary"><VizChart kind="iso" /></div>
            <div class="flex flex-wrap items-center gap-2 mt-3 pt-2.5 border-t border-border/50">
              <span class="inline-flex items-center rounded-lg border px-2.5 py-1 text-[11px] text-muted-foreground">Show as stacked bar</span>
              <span class="inline-flex items-center rounded-lg border px-2.5 py-1 text-[11px] text-muted-foreground">Show as line trend</span>
              <span class="ape-chip ape-chip-redraw ml-auto">redraws skip the engine</span>
            </div>
          </div>
        </div>
      </div>

    </section>

    <!-- ================= ONE QUESTION, EVERY SHAPE ================= -->
    <section class="relative overflow-hidden scene-3d">
      <div class="orb orb-violet orb-float-a h-72 w-72 -right-24 top-0" />
      <div class="max-w-6xl mx-auto px-4 lg:px-6 py-24">
        <div v-reveal class="text-center space-y-3 mb-10">
          <span class="ape-chip ape-chip-strategy">why shape matters</span>
          <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em]">One question, every shape</h2>
          <p class="text-sm text-muted-foreground max-w-2xl mx-auto">
            “How did Q3 revenue break down?”, same correct answer, rendered four ways.
            APE learns which shape <em>you</em> reach for, then leads with it.
          </p>
        </div>

        <div v-reveal="120" class="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <!-- 3D bar plot -->
          <div class="shape-card rise-in rounded-2xl border bg-card/70 glass-panel p-4 viz-card" :style="{ '--stagger': '0s' }">
            <div class="flex items-center justify-between mb-2">
              <span class="ape-chip ape-chip-strategy">3D bars</span>
              <span class="text-[10px] text-muted-foreground">visual</span>
            </div>
            <div class="h-28 text-primary"><VizChart kind="iso" /></div>
          </div>

          <!-- donut share -->
          <div class="shape-card rise-in rounded-2xl border bg-card/70 glass-panel p-4 viz-card" :style="{ '--stagger': '0.08s' }">
            <div class="flex items-center justify-between mb-2">
              <span class="ape-chip ape-chip-strategy">breakdown</span>
              <span class="text-[10px] text-muted-foreground">visual</span>
            </div>
            <div class="h-28 text-primary flex items-center justify-center"><VizChart kind="donut" /></div>
          </div>

          <!-- comparison table -->
          <div class="shape-card rise-in rounded-2xl border bg-card/70 glass-panel p-4" :style="{ '--stagger': '0.16s' }">
            <div class="flex items-center justify-between mb-2">
              <span class="ape-chip ape-chip-strategy">table</span>
              <span class="text-[10px] text-muted-foreground">text</span>
            </div>
            <div class="h-28 text-xs">
              <div class="grid grid-cols-2 gap-x-2 gap-y-1.5">
                <div class="text-muted-foreground">Cloud</div><div class="text-right font-medium tabular-nums">$47.5B</div>
                <div class="text-muted-foreground">Devices</div><div class="text-right font-medium tabular-nums">$10.4B</div>
                <div class="text-muted-foreground">Services</div><div class="text-right font-medium tabular-nums">$6.1B</div>
                <div class="text-muted-foreground">Other</div><div class="text-right font-medium tabular-nums">$1.1B</div>
              </div>
              <div class="border-t mt-2 pt-1.5 grid grid-cols-2"><span class="text-muted-foreground">Total</span><span class="text-right font-semibold tabular-nums text-primary">$65.1B</span></div>
            </div>
          </div>

          <!-- bullet summary -->
          <div class="shape-card rise-in rounded-2xl border bg-card/70 glass-panel p-4" :style="{ '--stagger': '0.24s' }">
            <div class="flex items-center justify-between mb-2">
              <span class="ape-chip ape-chip-strategy">bullets</span>
              <span class="text-[10px] text-muted-foreground">text</span>
            </div>
            <ul class="h-28 text-xs space-y-2 text-foreground/85">
              <li class="flex gap-2"><span class="text-primary">•</span> Cloud led at <span class="font-medium">73%</span> of revenue</li>
              <li class="flex gap-2"><span class="text-primary">•</span> Devices held steady near <span class="font-medium">$10B</span></li>
              <li class="flex gap-2"><span class="text-primary">•</span> Services grew fastest, <span class="font-medium">+18%</span></li>
              <li class="flex gap-2"><span class="text-primary">•</span> Other remained immaterial</li>
            </ul>
          </div>
        </div>
        <p class="text-center text-xs text-muted-foreground mt-5">
          Hover a card, the one you’d pick is the one APE learns to serve first.
        </p>
      </div>
    </section>

    <!-- ================= THE BRAIN / PERSONALISATION MAP ================= -->
    <section id="brain" class="relative overflow-hidden scroll-mt-16">
      <div class="orb orb-violet orb-float-a h-96 w-96 -left-32 top-24" />
      <div class="max-w-6xl mx-auto px-4 lg:px-6 py-24">
        <div v-reveal class="text-center space-y-3 mb-12">
          <span class="ape-chip ape-chip-strategy">inside the memory</span>
          <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em]">
            A memory of <span class="text-foreground">how you think</span>
          </h2>
          <p class="text-sm text-muted-foreground max-w-2xl mx-auto">
            Like a brain strengthening the pathways it uses, APE builds a preference map for every
            user, which shapes work, for which kinds of questions, in which domain.
          </p>
        </div>

        <!-- domains strip, the map keys itself by whatever your traffic carries -->
        <div v-reveal="60" class="mb-12">
          <div class="marquee-mask">
            <div class="marquee marquee-slow marquee-reverse flex items-center gap-2.5 w-max px-1 py-1">
              <span
                v-for="(d, i) in [...domainStrip, ...domainStrip]"
                :key="'dom' + i"
                class="inline-flex items-center gap-2 whitespace-nowrap rounded-full border bg-card/70 glass-panel px-3.5 py-2 text-[12px] text-foreground/90 shrink-0"
              >
                <span class="h-1.5 w-1.5 rounded-full shrink-0" :style="{ background: d.dot }" />
                {{ d.name }}
              </span>
            </div>
          </div>
          <p class="text-center text-[11px] text-muted-foreground/70 mt-2">
            …and any domain your traffic carries, nothing here is hardcoded
          </p>
        </div>

        <div v-reveal="100" class="grid lg:grid-cols-[0.95fr_1.05fr] gap-8 items-center mb-12">
          <!-- living neural brain -->
          <div class="relative rounded-3xl border bg-card/60 glass-panel p-6">
            <div class="h-[320px]">
              <NeuralBrain />
            </div>
            <div class="flex items-center justify-center gap-2 flex-wrap">
              <span class="ape-chip ape-chip-strategy">preference pathways</span>
              <span class="ape-chip">strengthen with every reaction</span>
            </div>
          </div>

          <!-- understand → map → serve -->
          <div class="space-y-4">
            <div
              v-for="(s, i) in brainSteps"
              :key="s.title"
              class="flex gap-4 rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover"
            >
              <div class="h-9 w-9 shrink-0 rounded-lg bg-primary/12 border border-primary/30 flex items-center justify-center text-sm font-bold text-primary">
                {{ i + 1 }}
              </div>
              <div>
                <h3 class="font-semibold text-sm">{{ s.title }}</h3>
                <p class="text-xs text-muted-foreground leading-relaxed mt-1">{{ s.body }}</p>
              </div>
            </div>
            <p class="text-xs text-muted-foreground/80 pl-1">
              The result is simple to feel: answers land right the first time, so users stop
              re-asking and reformatting, less friction, more signal.
            </p>
          </div>
        </div>

        <!-- domain preference profiles -->
        <div v-reveal="120" class="grid md:grid-cols-2 gap-4 mb-8">
          <div
            v-for="dom in domains"
            :key="dom.name"
            class="rounded-2xl border bg-card/70 glass-panel p-6 tilt-3d tilt-hover space-y-4"
          >
            <div class="flex items-center justify-between">
              <div>
                <h3 class="font-semibold">{{ dom.name }}</h3>
                <div class="text-[11px] text-muted-foreground">{{ dom.user }}</div>
              </div>
              <span class="ape-chip">learned profile</span>
            </div>
            <div class="space-y-3">
              <div v-for="(p, pi) in dom.prefs" :key="p.intent">
                <div class="flex items-center justify-between text-xs mb-1.5">
                  <span class="text-muted-foreground">{{ p.intent }}
                    <span class="text-foreground/85 font-medium"> → {{ p.format }}</span>
                  </span>
                  <span class="tabular-nums text-primary font-medium">{{ Math.round(p.v * 100) }}%</span>
                </div>
                <div class="h-1.5 rounded-full bg-muted/60 overflow-hidden">
                  <div
                    class="pref-bar h-full rounded-full bg-gradient-to-r from-teal-500 to-teal-400"
                    :style="{ width: p.v * 100 + '%', animationDelay: pi * 0.15 + 's' }"
                  />
                </div>
              </div>
            </div>
            <p class="text-[11px] text-muted-foreground/80 italic">“{{ dom.insight }}”</p>
          </div>
        </div>

        <div v-reveal="140" class="text-center space-y-3">
          <p class="text-xs text-muted-foreground">Illustrative profiles, the engine is domain-agnostic. Point it at yours:</p>
          <div class="flex items-center justify-center gap-2 flex-wrap max-w-2xl mx-auto">
            <span v-for="m in moreDomains" :key="m" class="ape-chip">{{ m }}</span>
            <span class="ape-chip ape-chip-strategy">+ yours</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= COGNITIVE FACETS ================= -->
    <section id="facets" class="relative max-w-6xl mx-auto px-4 lg:px-6 py-24 scroll-mt-16">
      <div v-reveal class="text-center space-y-3 mb-12">
        <span class="eyebrow">the portrait, not a number</span>
        <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em]">Cognitive facets</h2>
        <p class="text-sm text-muted-foreground max-w-2xl mx-auto">
          The map isn’t one preference, it’s a confidence-scored cell for every <em>kind of thinking</em>
          a user does. Each facet tracks its own leading strategy, evidence count, and certainty.
        </p>
      </div>

      <div v-reveal="120" class="grid md:grid-cols-3 gap-4">
        <div
          v-for="f in facets"
          :key="f.name"
          class="rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover space-y-4"
        >
          <div class="flex items-start gap-4">
            <!-- score ring -->
            <svg viewBox="0 0 56 56" class="h-14 w-14 shrink-0" aria-hidden="true">
              <circle cx="28" cy="28" r="24" fill="none" stroke="currentColor" stroke-opacity="0.12" stroke-width="4.5" />
              <circle
                cx="28" cy="28" r="24" fill="none" class="viz-arc"
                stroke="var(--primary)" stroke-width="4.5" stroke-linecap="round"
                :stroke-dasharray="`${(f.score / 100) * RING_C} ${RING_C}`"
                :style="{ '--len': RING_C + 'px', '--off': '0px' }"
              />
              <text x="28" y="32" text-anchor="middle" class="fill-foreground" font-size="14" font-weight="700">{{ f.score }}</text>
            </svg>
            <div class="min-w-0">
              <h3 class="font-semibold text-sm leading-snug">{{ f.name }}</h3>
              <div class="flex items-center gap-1.5 mt-1.5 flex-wrap">
                <span class="ape-chip">{{ f.domain }}</span>
                <span class="ape-chip" :class="f.score >= 85 ? 'ape-chip-pos' : ''">{{ f.tier }}</span>
              </div>
            </div>
          </div>
          <div class="rounded-xl border bg-background/50 px-3 py-2.5 flex items-center justify-between text-xs">
            <span class="text-muted-foreground">leads with <span class="text-foreground font-medium">{{ f.lead }}</span></span>
            <span class="tabular-nums text-primary font-medium">μ {{ f.mu.toFixed(2) }}</span>
          </div>
          <p class="text-xs text-muted-foreground leading-relaxed">{{ f.insight }}</p>
          <div class="text-[10px] text-muted-foreground/70">{{ f.n }} interactions · confidence grows with evidence</div>
        </div>
      </div>
      <p v-reveal="160" class="text-center text-[11px] text-muted-foreground/70 mt-6">
        Illustrative facets, every cell is recomputed live from real reactions, never frozen into a static persona.
      </p>
    </section>

    <!-- ================= GLOBAL INTELLIGENCE ================= -->
    <section id="global" class="relative overflow-hidden bg-dotgrid scroll-mt-16">
      <div class="orb orb-cyan orb-float-a h-80 w-80 -right-28 top-16" />
      <div class="max-w-6xl mx-auto px-4 lg:px-6 py-24">
        <div v-reveal class="text-center space-y-3 mb-12">
          <span class="ape-chip ape-chip-strategy">the crowd layer</span>
          <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em]">
            One user teaches one.
            <span class="text-foreground">Everyone teaches everyone.</span>
          </h2>
          <p class="text-sm text-muted-foreground max-w-2xl mx-auto">
            Every reaction also sharpens a global picture, what’s trending, where the questions come
            from, and which strategies win. New users start from the crowd’s best, then diverge into
            their own map.
          </p>
        </div>

        <div v-reveal="120" class="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          <!-- trending topics -->
          <div class="rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-sm">Trending topics</h3>
              <span class="ape-chip">this week</span>
            </div>
            <div class="space-y-2.5">
              <div
                v-for="tp in trendingTopics"
                :key="tp.t"
                class="flex items-center justify-between rounded-xl border bg-background/50 px-3 py-2"
              >
                <span class="text-xs">{{ tp.t }}</span>
                <span class="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400 tabular-nums">
                  <ArrowTrendingUpIcon class="h-3 w-3" /> {{ tp.d }}
                </span>
              </div>
            </div>
          </div>

          <!-- domain share -->
          <div class="rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-sm">Where questions live</h3>
              <span class="ape-chip">by domain</span>
            </div>
            <div class="space-y-3.5">
              <div v-for="(dm, di) in domainShare" :key="dm.name">
                <div class="flex items-center justify-between text-xs mb-1.5">
                  <span class="text-muted-foreground">{{ dm.name }}</span>
                  <span class="tabular-nums text-foreground/85 font-medium">{{ dm.v }}%</span>
                </div>
                <div class="h-1.5 rounded-full bg-muted/60 overflow-hidden">
                  <div
                    class="pref-bar h-full rounded-full bg-gradient-to-r from-teal-500 to-teal-400"
                    :style="{ width: dm.v * 2.4 + '%', animationDelay: di * 0.12 + 's' }"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- winning strategies -->
          <div class="rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover md:col-span-2 lg:col-span-1">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-sm">Winning strategies</h3>
              <span class="ape-chip ape-chip-pos">global win rate</span>
            </div>
            <div class="space-y-2.5">
              <div
                v-for="w in winningStrategies"
                :key="w.q"
                class="rounded-xl border bg-background/50 px-3 py-2.5"
              >
                <div class="flex items-center justify-between text-xs">
                  <span class="text-muted-foreground">{{ w.q }}
                    <span class="text-foreground/85 font-medium"> → {{ w.f }}</span>
                  </span>
                  <span class="tabular-nums text-primary font-medium">{{ w.v }}%</span>
                </div>
              </div>
            </div>
            <p class="text-[11px] text-muted-foreground/80 mt-4 leading-relaxed">
              These global priors warm-start every new user, nobody begins from zero, and nobody stays generic.
            </p>
          </div>
        </div>

        <div v-reveal="160" class="mt-8 mx-auto max-w-3xl rounded-2xl border bg-card/70 glass-panel p-5 flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-[11px] text-muted-foreground">
          <span class="inline-flex items-center gap-1.5"><ShieldCheckIcon class="h-3.5 w-3.5 text-primary" /> learned from hashed identities</span>
          <span class="inline-flex items-center gap-1.5"><ShieldCheckIcon class="h-3.5 w-3.5 text-primary" /> no message content stored</span>
          <span class="inline-flex items-center gap-1.5"><ShieldCheckIcon class="h-3.5 w-3.5 text-primary" /> illustrative figures, computed live in production</span>
        </div>
      </div>
    </section>

    <!-- ================= FEATURES ================= -->
    <section id="features" class="relative max-w-6xl mx-auto px-4 lg:px-6 py-24 scroll-mt-20">
      <div v-reveal class="text-center space-y-3 mb-10">
        <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em]">Built around one idea</h2>
        <p class="text-sm text-muted-foreground max-w-2xl mx-auto">
          Being correct includes being usable. Everything below exists to make the right answer
          arrive in the right shape, and keep getting better at it.
        </p>
      </div>
      <div v-reveal="120" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="(f, i) in features"
          :key="f.title"
          class="rise-in rounded-2xl border bg-card/70 glass-panel p-6 tilt-3d tilt-hover space-y-3"
          :style="{ '--stagger': (i % 3) * 0.07 + 's' }"
        >
          <div class="h-10 w-10 rounded-xl bg-primary/12 border border-primary/30 flex items-center justify-center">
            <component :is="f.icon" class="h-5 w-5 text-primary" />
          </div>
          <h3 class="font-semibold">{{ f.title }}</h3>
          <p class="text-sm text-muted-foreground leading-relaxed">{{ f.body }}</p>
        </div>
      </div>
    </section>

    <!-- ================= VISUALIZATION GALLERY ================= -->
    <section class="relative overflow-hidden bg-dotgrid">
      <div class="orb orb-cyan orb-float-b h-80 w-80 -left-28 top-10" />
      <div class="orb orb-emerald orb-float-a h-64 w-64 right-0 bottom-0" />
      <div class="max-w-6xl mx-auto px-4 lg:px-6 py-24">
        <div v-reveal class="text-center space-y-3 mb-10">
          <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em]">
            Visuals, <span class="text-foreground">rendered live</span>
          </h2>
          <p class="text-sm text-muted-foreground max-w-2xl mx-auto">
            When an answer carries real data, it arrives as an interactive chart, 33 kinds, 2D and 3D,
            drawn from governed components, never fabricated.
          </p>
        </div>

        <!-- FLAGSHIP: a fully interactive chart, crosshair, tooltip, legend toggles -->
        <div v-reveal="80" class="rounded-3xl border bg-card/70 glass-panel p-5 lg:p-7 mb-6">
          <div class="flex items-center justify-between flex-wrap gap-2 mb-4">
            <div>
              <h3 class="font-semibold">A year of learning, by format</h3>
              <p class="text-[11px] text-muted-foreground mt-0.5">Win rate of each pairing as reactions accumulate, the divergence <em>is</em> the personalisation.</p>
            </div>
            <span class="ape-chip ape-chip-strategy">fully interactive</span>
          </div>
          <InteractiveChart />
        </div>

        <div v-reveal="120" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div class="rise-in rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover viz-card" :style="{ '--stagger': '0s' }" @pointerenter="rep('area')">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-sm">Trends over time</h3>
              <span class="ape-chip">line · area</span>
            </div>
            <div class="h-32 text-cyan-500"><VizChart :key="'a' + (galleryReplay.area || 0)" kind="area" /></div>
          </div>

          <div class="rise-in rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover viz-card" :style="{ '--stagger': '0.07s' }" @pointerenter="rep('bars')">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-sm">Rankings &amp; totals</h3>
              <span class="ape-chip">bar</span>
            </div>
            <div class="h-32 text-teal-600 dark:text-teal-400"><VizChart :key="'b' + (galleryReplay.bars || 0)" kind="bars" /></div>
          </div>

          <div class="rise-in rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover viz-card" :style="{ '--stagger': '0.14s' }" @pointerenter="rep('iso')">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-sm">3D breakdown</h3>
              <span class="ape-chip ape-chip-strategy">3D bars</span>
            </div>
            <div class="h-32 text-primary"><VizChart :key="'i' + (galleryReplay.iso || 0)" kind="iso" /></div>
          </div>

          <div class="rise-in rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover viz-card" :style="{ '--stagger': '0.21s' }" @pointerenter="rep('donut')">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-sm">Composition</h3>
              <span class="ape-chip">donut · pie</span>
            </div>
            <div class="h-32 text-primary flex items-center justify-center"><VizChart :key="'d' + (galleryReplay.donut || 0)" kind="donut" /></div>
          </div>

          <div class="rise-in rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover viz-card" :style="{ '--stagger': '0.28s' }" @pointerenter="rep('radar')">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-sm">Multi-factor</h3>
              <span class="ape-chip">radar</span>
            </div>
            <div class="h-32 text-cyan-500 flex items-center justify-center"><VizChart :key="'r' + (galleryReplay.radar || 0)" kind="radar" /></div>
          </div>

          <div class="rise-in rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover viz-card" :style="{ '--stagger': '0.35s' }" @pointerenter="rep('bubbles')">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-sm">Distributions</h3>
              <span class="ape-chip">bubble · scatter</span>
            </div>
            <div class="h-32"><VizChart :key="'u' + (galleryReplay.bubbles || 0)" kind="bubbles" /></div>
          </div>

          <div class="rise-in rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover viz-card" :style="{ '--stagger': '0.42s' }" @pointerenter="rep('lines')">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-sm">Multi-series time</h3>
              <span class="ape-chip">timeseries · combo</span>
            </div>
            <div class="h-32 text-teal-600 dark:text-teal-300"><VizChart :key="'l' + (galleryReplay.lines || 0)" kind="lines" /></div>
          </div>

          <div class="rise-in rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover viz-card md:col-span-2 lg:col-span-2" :style="{ '--stagger': '0.49s' }" @pointerenter="rep('heat')">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-sm">Density &amp; intensity</h3>
              <span class="ape-chip">heatmap · matrix</span>
            </div>
            <div class="h-32"><VizChart :key="'h' + (galleryReplay.heat || 0)" kind="heat" /></div>
          </div>
        </div>
        <p v-reveal="160" class="text-center text-[11px] text-muted-foreground/70 mt-5">
          Hover any chart to watch it draw itself again, every visual in the product animates in live.
        </p>
      </div>
    </section>

    <!-- ================= THE LOOP ================= -->
    <section id="loop" class="relative overflow-hidden scroll-mt-20">
      <div class="orb orb-cyan orb-float-b h-72 w-72 -left-20 top-10" />
      <div class="max-w-6xl mx-auto px-4 lg:px-6 py-24">
        <div v-reveal class="text-center space-y-3 mb-10">
          <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em]">A loop, not a setting</h2>
          <p class="text-sm text-muted-foreground max-w-2xl mx-auto">
            There is no preferences panel. Every message runs the loop, and the loop runs in milliseconds.
          </p>
        </div>
        <div v-reveal="120" class="relative">
          <!-- animated pulse traveling through the four steps -->
          <div class="flow-line hidden lg:block" aria-hidden="true" />
          <div class="relative grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div
              v-for="(st, i) in loop"
              :key="st.n"
              class="rise-in relative rounded-2xl border bg-card/85 glass-panel p-6 tilt-3d tilt-hover"
              :style="{ '--stagger': i * 0.08 + 's' }"
            >
              <div class="text-[32px] font-bold text-foreground">{{ st.n }}</div>
              <div class="font-semibold mt-1">{{ st.title }}</div>
              <p class="text-xs text-muted-foreground mt-2 leading-relaxed">{{ st.body }}</p>
            </div>
          </div>
        </div>
        <div class="mt-8 mx-auto max-w-2xl rounded-2xl border bg-card/70 glass-panel p-5 text-center">
          <div class="font-mono text-sm text-muted-foreground">
            next pick = proven results + a measured dose of curiosity
          </div>
          <div class="text-[11px] text-muted-foreground mt-1.5">
            <span class="text-primary font-medium">lean on what works</span> · <span class="text-teal-600 dark:text-teal-400 font-medium">keep testing what might</span>
            · computed live on every pick, never cached, never stale
          </div>
        </div>
      </div>
    </section>

    <!-- ================= PLUG AND PLAY ================= -->
    <section class="relative overflow-hidden bg-dotgrid">
      <div class="orb orb-violet orb-float-b h-72 w-72 -left-24 top-10" />
      <div class="max-w-6xl mx-auto px-4 lg:px-6 py-24">
        <div v-reveal class="text-center space-y-3 mb-10">
          <span class="ape-chip ape-chip-strategy">plug &amp; play</span>
          <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em]">
            Sits on top of <span class="text-foreground">your stack</span>
          </h2>
          <p class="text-sm text-muted-foreground max-w-2xl mx-auto">
            Your memory layer, vector store, RAG, and agents keep doing their job. APE is the headless
            service that owns the one decision they don’t, the format, slotting in between what generates
            the answer and what renders it, with a single call.
          </p>
        </div>

        <!-- live architecture: where APE sits in a RAG / agentic stack -->
        <div v-reveal="100" class="rounded-3xl border bg-card/60 glass-panel p-4 lg:p-8 mb-8 overflow-hidden">
          <div class="flex items-center justify-between flex-wrap gap-2 mb-4">
            <div class="flex items-center gap-2">
              <h3 class="font-semibold">Inside your stack</h3>
              <span class="ape-chip ape-chip-strategy">live flow</span>
            </div>
            <div class="flex items-center gap-2 text-[11px] text-muted-foreground">
              <span class="inline-flex items-center gap-1.5"><span class="h-1.5 w-4 rounded-full bg-primary inline-block" /> signal path</span>
              <span class="ape-chip">agents · RAG · tools all untouched</span>
            </div>
          </div>
          <ArchFlow />
          <p class="text-[11px] text-muted-foreground mt-3 text-center">
            Your orchestrator, retriever, vector store and tools stay exactly as they are.
            APE is the one glowing decision between them and the synthesizer.
          </p>
        </div>

        <div v-reveal="120" class="grid lg:grid-cols-[1fr_0.9fr] gap-5 items-stretch">
          <!-- integration cards -->
          <div class="grid sm:grid-cols-2 gap-3">
            <div
              v-for="(it, i) in integrations"
              :key="it.title"
              class="rise-in rounded-2xl border bg-card/70 glass-panel p-5 tilt-3d tilt-hover space-y-2"
              :style="{ '--stagger': (i % 2) * 0.06 + 's' }"
            >
              <div class="h-9 w-9 rounded-lg bg-primary/12 border border-primary/30 flex items-center justify-center">
                <component :is="it.icon" class="h-4.5 w-4.5 text-primary" />
              </div>
              <h3 class="font-semibold text-sm">{{ it.title }}</h3>
              <p class="text-xs text-muted-foreground leading-relaxed">{{ it.body }}</p>
            </div>
          </div>

          <!-- one-call contract -->
          <div class="rise-in rounded-2xl border bg-card/70 glass-panel p-5 flex flex-col" style="--stagger: 0.1s">
            <div class="flex items-center gap-2 mb-3">
              <span class="ape-chip">one call</span>
              <span class="text-[11px] text-muted-foreground">no SDK · language-agnostic</span>
            </div>
            <pre class="flex-1 text-[11.5px] leading-relaxed font-mono text-muted-foreground overflow-x-auto rounded-xl border bg-background/50 p-4"><span class="text-primary">POST</span> /turn
{
  <span class="text-foreground/80">"user_id"</span>: "u_42",
  <span class="text-foreground/80">"session_id"</span>: "s_9",
  <span class="text-foreground/80">"classification"</span>: { "intent": "comparison" },
  <span class="text-foreground/80">"signals"</span>: ["thumbs_up"]   <span class="text-muted-foreground/60">// reaction to last answer</span>
}

<span class="text-teal-600 dark:text-teal-300">→</span> {
  <span class="text-foreground/80">"selected_strategy"</span>: "comparison_table",
  <span class="text-foreground/80">"instruction"</span>: {
    "text": "Present the options as a
             side-by-side comparison table."
  }
}</pre>
            <p class="text-[11px] text-muted-foreground mt-3">
              You send the intent + the user’s reaction. You get back a format directive for your synthesizer. That’s the whole contract.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= TECH STACK ================= -->
    <section class="relative max-w-6xl mx-auto px-4 lg:px-6 py-24">
      <div v-reveal class="text-center space-y-3 mb-10">
        <span class="eyebrow">engineered with</span>
        <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em]">Built on a serious stack</h2>
        <p class="text-sm text-muted-foreground max-w-2xl mx-auto">
          A statistics core, a governed visualization layer, and a serverless backend, production tools, not a toy demo.
        </p>
      </div>
      <div v-reveal="120" class="rise-in space-y-3">
        <!-- row A: drifts left -->
        <div class="marquee-mask">
          <div class="marquee marquee-slow flex items-stretch gap-3 w-max px-1 py-1">
            <div
              v-for="(t, i) in [...techRowA, ...techRowA, ...techRowA, ...techRowA]"
              :key="'a' + i"
              class="flex items-center gap-3 rounded-2xl border bg-card/70 glass-panel p-4 w-[230px] shrink-0"
            >
              <div class="h-10 w-10 shrink-0 rounded-xl border border-border bg-background/40 flex items-center justify-center p-2" :class="t.color">
                <TechGlyph :name="t.key" />
              </div>
              <div class="min-w-0">
                <div class="font-medium text-sm truncate">{{ t.name }}</div>
                <div class="text-[11px] text-muted-foreground truncate">{{ t.role }}</div>
              </div>
            </div>
          </div>
        </div>
        <!-- row B: drifts right -->
        <div class="marquee-mask">
          <div class="marquee marquee-slow marquee-reverse flex items-stretch gap-3 w-max px-1 py-1">
            <div
              v-for="(t, i) in [...techRowB, ...techRowB, ...techRowB, ...techRowB]"
              :key="'b' + i"
              class="flex items-center gap-3 rounded-2xl border bg-card/70 glass-panel p-4 w-[230px] shrink-0"
            >
              <div class="h-10 w-10 shrink-0 rounded-xl border border-border bg-background/40 flex items-center justify-center p-2" :class="t.color">
                <TechGlyph :name="t.key" />
              </div>
              <div class="min-w-0">
                <div class="font-medium text-sm truncate">{{ t.name }}</div>
                <div class="text-[11px] text-muted-foreground truncate">{{ t.role }}</div>
              </div>
            </div>
          </div>
        </div>
        <p class="text-center text-[11px] text-muted-foreground/70 pt-1">hover to pause</p>
      </div>
    </section>

    <!-- ================= FAQ ================= -->
    <section id="faq" class="relative max-w-6xl mx-auto px-4 lg:px-6 py-24 scroll-mt-16">
      <div v-reveal class="grid lg:grid-cols-[1fr_2fr] gap-10 lg:gap-16 items-start">
        <div class="lg:sticky lg:top-24 space-y-4">
          <span class="eyebrow">straight answers</span>
          <h2 class="text-4xl lg:text-5xl font-semibold tracking-[-0.03em] leading-[1.06] text-balance">
            Questions teams
            <span class="text-muted-foreground">actually ask.</span>
          </h2>
          <p class="text-sm lg:text-base text-muted-foreground leading-relaxed max-w-sm">
            The short versions. For the full mechanics of selection, rewards and attribution,
            see <RouterLink to="/about" class="text-primary hover:underline underline-offset-4">how it works</RouterLink>.
          </p>
        </div>

        <div class="space-y-2.5">
          <div
            v-for="(f, i) in faqs"
            :key="i"
            v-reveal="i * 50"
            class="rise-in rounded-2xl border bg-card/70 glass-panel overflow-hidden transition-colors"
            :class="openFaq === i ? 'border-teal-400/30' : ''"
          >
            <button
              type="button"
              class="w-full flex items-center justify-between gap-4 px-5 py-4 text-left cursor-pointer hover:bg-secondary/30 transition-colors"
              :aria-expanded="openFaq === i"
              :aria-controls="'faq-panel-' + i"
              @click="toggleFaq(i)"
            >
              <span class="text-[14.5px] font-medium leading-snug">{{ f.q }}</span>
              <span
                class="shrink-0 h-6 w-6 rounded-full border flex items-center justify-center text-muted-foreground transition-transform duration-300"
                :class="openFaq === i ? 'rotate-45 border-teal-400/40 text-primary' : ''"
                aria-hidden="true"
              >
                <svg viewBox="0 0 12 12" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                  <path d="M6 1v10M1 6h10" />
                </svg>
              </span>
            </button>
            <div :id="'faq-panel-' + i" class="faq-body" :class="{ 'faq-open': openFaq === i }">
              <div class="overflow-hidden">
                <p class="px-5 pb-5 text-[13px] text-muted-foreground leading-relaxed">{{ f.a }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= CTA ================= -->
    <section class="relative overflow-hidden">
      <div class="orb orb-violet orb-float-a h-80 w-80 -right-24 -top-10" />
      <div class="orb orb-cyan orb-float-b h-64 w-64 left-10 bottom-0" />
      <div class="max-w-6xl mx-auto px-4 lg:px-6 pb-20 pt-4">
        <div class="relative rounded-3xl border glass-panel p-10 lg:p-14 text-center overflow-hidden">
          <div class="relative space-y-5">
            <h2 class="text-3xl lg:text-4xl font-semibold tracking-tight text-balance">
              Ask it something. Then tell it what you think.
            </h2>
            <p class="text-sm text-muted-foreground max-w-xl mx-auto">
              Create a free account and every thumbs-up and every “make it a table” quietly
              teaches it your preference, kept for you across every device.
            </p>
            <Button v-magnet :to="loggedIn ? '/app/chat' : '/login?mode=register'" class="btn-shine h-12 px-9 text-sm gap-2 shadow-lg shadow-black/30">
              <ChatBubbleLeftRightIcon class="h-4 w-4" />
              {{ loggedIn ? 'Launch APE' : 'Create your free account' }}
            </Button>
          </div>
        </div>
      </div>
    </section>

    </main>

    <!-- ================= FOOTER ================= -->
    <footer class="border-t/70">
      <div class="max-w-6xl mx-auto px-4 lg:px-6 pt-14 pb-8">
        <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-10 pb-10">
          <!-- brand -->
          <div class="space-y-3 lg:col-span-2 max-w-sm">
            <div class="flex items-center gap-2.5">
              <svg viewBox="0 0 100 100" class="h-8 w-8" aria-hidden="true">
                <rect x="2" y="2" width="96" height="96" rx="27" fill="#15140d" />
                <rect x="26" y="31" width="48" height="9" rx="4" fill="#f4f4ec" />
                <rect x="26" y="46" width="48" height="9" rx="4" fill="#14b8a6" />
                <rect x="26" y="61" width="32" height="9" rx="4" fill="#6b6b5e" />
              </svg>
              <span class="font-semibold">APE</span>
            </div>
            <p class="text-xs text-muted-foreground leading-relaxed">
              The Adaptive Personalisation Engine. One headless call between your model and
              your user, learning the shape every answer should take.
            </p>
            <p class="text-[11px] text-muted-foreground/70">The LLM owns the content · APE owns the format</p>
          </div>
          <!-- product -->
          <div class="space-y-3">
            <div class="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Product</div>
            <div class="grid gap-2 text-sm">
              <RouterLink to="/app/chat" class="text-muted-foreground hover:text-foreground transition w-fit">Chat</RouterLink>
              <a href="#playground" class="text-muted-foreground hover:text-foreground transition w-fit">Live playground</a>
              <a href="#features" class="text-muted-foreground hover:text-foreground transition w-fit">Features</a>
              <a href="#loop" class="text-muted-foreground hover:text-foreground transition w-fit">How it learns</a>
              <a href="#faq" class="text-muted-foreground hover:text-foreground transition w-fit">FAQ</a>
            </div>
          </div>
          <!-- company -->
          <div class="space-y-3">
            <div class="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Learn more</div>
            <div class="grid gap-2 text-sm">
              <RouterLink to="/about" class="text-muted-foreground hover:text-foreground transition w-fit">About</RouterLink>
              <RouterLink to="/app/settings" class="text-muted-foreground hover:text-foreground transition w-fit">Settings</RouterLink>
            </div>
          </div>
        </div>
        <div class="border-t pt-6 flex flex-wrap items-center justify-between gap-3 text-[11px] text-muted-foreground/70">
          <span>© 2026 APE · Adaptive Personalisation Engine</span>
          <span>~3 ms decisions · 18 formats · 9 signals · 6 intents</span>
        </div>
      </div>
    </footer>

  </div>
</template>
