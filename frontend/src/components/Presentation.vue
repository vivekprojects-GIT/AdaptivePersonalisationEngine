<!--
  Presentation — a fullscreen, TRON-styled deck of the APE story (from the
  "Adaptive Presentation Engine" deck). Keyboard nav (←/→/Space, Esc),
  dot indicators, and a real "Present" fullscreen mode. Slides scale crisply
  with the stage via container-query units (cqw/cqh).
-->
<template>
  <div ref="root" class="deck" tabindex="0" role="dialog" aria-label="APE presentation">
    <!-- top bar -->
    <header class="deck-bar">
      <div class="deck-brand">
        <span class="dot" /> APE<span class="brand-sub"> · The Adaptive Presentation Engine</span>
      </div>
      <div class="deck-actions">
        <span class="deck-count">{{ i + 1 }} / {{ slides.length }}</span>
        <button class="dbtn" title="Previous (←)" @click="prev"><svg viewBox="0 0 24 24"><path d="M15 6l-6 6 6 6" /></svg></button>
        <button class="dbtn" title="Next (→)" @click="next"><svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6" /></svg></button>
        <button class="dbtn dbtn-accent" :title="presenting ? 'Exit full screen' : 'Present (full screen)'" @click="togglePresent">
          <svg v-if="!presenting" viewBox="0 0 24 24"><path d="M4 9V5h4M20 9V5h-4M4 15v4h4M20 15v4h-4" /></svg>
          <svg v-else viewBox="0 0 24 24"><path d="M9 4v4H5M15 4v4h4M9 20v-4H5M15 20v-4h4" /></svg>
          <span class="dbtn-label">{{ presenting ? 'Exit' : 'Present' }}</span>
        </button>
        <button class="dbtn" title="Close (Esc)" @click="close"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" /></svg></button>
      </div>
    </header>

    <!-- stage -->
    <div class="deck-stagewrap">
      <div class="stage">
        <Transition name="sfade" mode="out-in">
          <div class="slide-host" :key="i">
          <!-- 0 · TITLE -->
          <section v-if="i === 0" class="slide slide-title">
            <div class="kicker">PERSONAL WEALTH · APRIL 2026</div>
            <h1>The Adaptive<br /><span class="hl">Presentation Engine</span></h1>
            <p class="lead">Learning the right way to answer — for every kind of question.</p>
            <div class="title-orbs"><span /><span /><span /><span /><span /><span /></div>
          </section>

          <!-- 1 · THE PROBLEM -->
          <section v-else-if="i === 1" class="slide">
            <div class="s-head"><span class="ey">the problem we're solving</span><h2>Same question. Different users. Different needs.</h2></div>
            <div class="two-col">
              <div class="persona">
                <div class="p-top"><span class="p-ava">S</span><div><b>Sarah, 58</b><i>Pre-retiree, deliberate</i></div></div>
                <p class="p-q">"Should I do a Roth conversion?"</p>
                <p class="p-want">Wants a <b>clear recommendation</b>, then the reasoning.</p>
                <div class="p-fmt">Best format · <b>Decision Card</b></div>
              </div>
              <div class="persona">
                <div class="p-top"><span class="p-ava">M</span><div><b>Marcus, 42</b><i>Engineer, analytical</i></div></div>
                <p class="p-q">"Should I do a Roth conversion?"</p>
                <p class="p-want">Wants a <b>side-by-side comparison</b> to decide for himself.</p>
                <div class="p-fmt">Best format · <b>Comparison Table</b></div>
              </div>
            </div>
          </section>

          <!-- 2 · FIXED → ADAPTIVE -->
          <section v-else-if="i === 2" class="slide slide-center">
            <span class="ey">what APE does</span>
            <h2 class="big">From black-box, fixed LLM formats<br />to <span class="hl">adaptive responses</span>.</h2>
            <p class="lead">APE learns the most effective output format for each category of user
              question — by analysing interaction patterns and engagement signals over time.</p>
            <div class="arrow-row"><span class="pill dim">Fixed format</span><span class="arr">→</span><span class="pill on">Adaptive format</span></div>
          </section>

          <!-- 3 · DECIDE -->
          <section v-else-if="i === 3" class="slide">
            <div class="s-head"><span class="ey">six things users come to ask</span><h2>The <span class="hl">DECIDE</span> model</h2></div>
            <div class="decide-grid">
              <div v-for="d in decide" :key="d.k" class="dcard">
                <span class="dletter">{{ d.k }}</span>
                <b>{{ d.name }}</b>
                <i>{{ d.q }}</i>
                <span class="dneeds">{{ d.need }}</span>
              </div>
            </div>
          </section>

          <!-- 4 · THE LOOP -->
          <section v-else-if="i === 4" class="slide">
            <div class="s-head"><span class="ey">how the loop works</span><h2>Every turn is a learning opportunity</h2></div>
            <div class="loop-row">
              <template v-for="(s, n) in loop" :key="s.t">
                <div class="lstep"><span class="lnum">{{ n + 1 }}</span><b>{{ s.t }}</b><i>{{ s.d }}</i></div>
                <span v-if="n < loop.length - 1" class="larr">→</span>
              </template>
            </div>
            <p class="foot">Belief updates feed the next decision — repeated forever.</p>
          </section>

          <!-- 5 · FORMAT MENU -->
          <section v-else-if="i === 5" class="slide">
            <div class="s-head"><span class="ey">a small menu of formats per intent</span><h2>Meaningful choices to learn between</h2></div>
            <div class="menu">
              <div class="menu-head"><span>Intent</span><span>Option A</span><span>Option B</span><span>Option C</span></div>
              <div v-for="m in menu" :key="m[0]" class="menu-row">
                <span class="mi">{{ m[0] }}</span><span>{{ m[1] }}</span><span>{{ m[2] }}</span><span>{{ m[3] }}</span>
              </div>
            </div>
          </section>

          <!-- 6 · CONTENT VS FORMAT -->
          <section v-else-if="i === 6" class="slide">
            <div class="s-head"><span class="ey">the key insight</span><h2>Not every "bad reaction" means the format was wrong</h2></div>
            <div class="two-col">
              <div class="insight neg">
                <span class="tag">FORMAT FAILURE</span>
                <p>"Can you make this shorter?"</p>
                <b>Penalize the format.</b> Try a shorter one next time.
              </div>
              <div class="insight warn">
                <span class="tag">CONTENT FAILURE</span>
                <p>"That doesn't account for my pension."</p>
                <b>Don't blame the format.</b> Log the content gap.
              </div>
            </div>
          </section>

          <!-- 7 · REWARD MODEL -->
          <section v-else-if="i === 7" class="slide">
            <div class="s-head"><span class="ey">how reactions become learning</span><h2>Two axes, never confused</h2></div>
            <div class="ledger">
              <div class="lrow lhead"><span>What the user does</span><span class="lc">Content</span><span class="lc">Format</span><span class="lm">What it means</span></div>
              <div v-for="r in reward" :key="r[0]" class="lrow">
                <span>{{ r[0] }}</span>
                <span class="lc"><b :class="cls(r[1])">{{ r[1] }}</b></span>
                <span class="lc"><b :class="cls(r[2])">{{ r[2] }}</b></span>
                <span class="lm">{{ r[3] }}</span>
              </div>
            </div>
            <p class="foot"><b>The protect rule:</b> a content failure never penalizes a format that worked.</p>
          </section>

          <!-- 8 · THE BANDIT -->
          <section v-else-if="i === 8" class="slide">
            <div class="s-head"><span class="ey">how APE picks a format</span><h2>Exploit what works · explore for better</h2></div>
            <div class="two-col">
              <div class="gauge"><div class="g-num">~85%</div><b>EXPLOIT</b><i>Pick the format with the best track record for this kind of question.</i></div>
              <div class="gauge alt"><div class="g-num">~15%</div><b>EXPLORE</b><i>Try a less-tested format — to see if it beats today's winner.</i></div>
            </div>
            <p class="foot"><b>Warm-up:</b> every new (Topic × Intent) cell tries each format once, then settles in — about 7 turns.</p>
          </section>

          <!-- 9 · WHAT THE USER SEES -->
          <section v-else-if="i === 9" class="slide">
            <div class="s-head"><span class="ey">what the user sees</span><h2>The intelligence is invisible. The improvement is felt.</h2></div>
            <div class="quad">
              <div class="qcard"><b>Invisible adaptation</b><i>The next response simply uses the better format. No transition language.</i></div>
              <div class="qcard"><b>Silent improvement</b><i>No "the engine chose this" labels, no exploration disclaimers.</i></div>
              <div class="qcard"><b>Safety valve</b><i>Ask for a format change 2+ times → a one-tap format chooser appears.</i></div>
              <div class="qcard"><b>Always-on feedback</b><i>Thumbs up / down stay visible — the highest-quality learning signal.</i></div>
            </div>
          </section>

          <!-- 10 · METRICS -->
          <section v-else-if="i === 10" class="slide">
            <div class="s-head"><span class="ey">how we'll know it's working</span><h2>One primary metric, three signals</h2></div>
            <div class="metric-hero"><div class="m-big">↓ x%</div><div><b>Reduction in repair prompts</b><i>rephrases + format-change requests + regenerates per session, within 3 months</i></div></div>
            <div class="metric-row">
              <div class="mc"><span class="mu">↑</span> Deeper follow-ups<i>content engagement</i></div>
              <div class="mc"><span class="mu">↓</span> Session abandons<i>overall usefulness</i></div>
              <div class="mc"><span class="mu">↑</span> Thumbs-up rate<i>user-stated success</i></div>
            </div>
          </section>

          <!-- 11 · V1 SCOPE + ROADMAP -->
          <section v-else-if="i === 11" class="slide">
            <div class="s-head"><span class="ey">scope</span><h2>V1 nails one thing well — format optimization</h2></div>
            <div class="two-col">
              <div class="scope in">
                <span class="tag on">IN V1</span>
                <ul><li v-for="x in v1" :key="x">{{ x }}</li></ul>
              </div>
              <div class="scope next">
                <span class="tag">V2 / V3 ROADMAP</span>
                <ul><li v-for="x in roadmap" :key="x.t"><b>{{ x.v }}</b> {{ x.t }}</li></ul>
              </div>
            </div>
          </section>

          <!-- 12 · CLOSING -->
          <section v-else class="slide slide-center">
            <span class="ey">APE V1 in one breath</span>
            <h2 class="big">Every conversation gets a little better<br />than the <span class="hl">last</span>.</h2>
            <p class="lead">Because we now know the difference between a <b>format problem</b> and a
              <b>content problem</b> — and never confuse the two when learning.</p>
            <div class="arrow-row"><span class="pill on">Format = measurable</span><span class="pill dim">Content stays the LLM's job</span><span class="pill on">Improvement is felt</span></div>
          </section>
          </div>
        </Transition>
      </div>
    </div>

    <!-- dots -->
    <footer class="deck-dots">
      <button v-for="(s, n) in slides" :key="n" class="dot-btn" :class="{ on: n === i }" :title="s.title" @click="go(n)" />
    </footer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'

const emit = defineEmits<{ (e: 'close'): void }>()

const slides = [
  { title: 'Title' }, { title: 'The problem' }, { title: 'Fixed → adaptive' },
  { title: 'The DECIDE model' }, { title: 'The loop' }, { title: 'Format menu' },
  { title: 'Content vs format' }, { title: 'Reward model' }, { title: 'The bandit' },
  { title: 'What the user sees' }, { title: 'Metrics' }, { title: 'V1 scope + roadmap' },
  { title: 'In one breath' },
]

const decide = [
  { k: 'D', name: 'Decision', q: '"Which one should I pick?"', need: 'A clear recommendation' },
  { k: 'E', name: 'Explanation', q: '"How does this work?"', need: 'A mental model' },
  { k: 'C', name: 'Comparison', q: '"How do these differ?"', need: 'Side-by-side view' },
  { k: 'I', name: 'Instructional', q: '"How do I do this?"', need: 'Step-by-step guide' },
  { k: 'D', name: 'Definitional', q: '"What is this?"', need: 'Quick definition' },
  { k: 'E', name: 'Evaluation', q: '"Am I doing this right?"', need: 'Validation of a plan' },
]
const loop = [
  { t: 'User asks', d: '"Should I do a Roth conversion?"' },
  { t: 'Classify', d: 'Topic + Intent (e.g. Decision)' },
  { t: 'Pick format', d: 'From a small set of proven options' },
  { t: 'Respond', d: 'LLM generates in chosen format' },
  { t: 'Learn', d: 'Watch reaction, update beliefs' },
]
const menu = [
  ['Decision', 'Decision Card', 'Pros / Cons Table', 'Step-by-step'],
  ['Explanation', 'Short Paragraph', 'Bullet Summary', 'Analogy'],
  ['Comparison', 'Comparison Table', 'Pros / Cons', 'Bullet Contrast'],
  ['Instructional', 'Numbered Steps', 'Checklist', 'Phased Workflow'],
  ['Definitional', 'One-liner', 'Definition + Example', 'Definition + Pointer'],
  ['Evaluation', 'Affirm + Calibrate', 'Affirm + Strengthen', 'Concerned Pushback'],
]
const reward = [
  ['Thumbs up', '+2', '+2', 'Both worked'],
  ['Copy / save', '+2', '+2', 'Worth keeping'],
  ['"Make it shorter"', '—', '−2', 'Pure format failure'],
  ['"That’s not right"', '−2', '—', 'Pure content failure'],
  ['Re-asks the question', '−1', '—', "Content didn't land"],
  ['Thumbs down', '−2', '−2', 'Both failed'],
  ['Regenerate', '−2', '−2', 'Wants something else'],
  ['Asks a deeper question', '+1', '—', 'Content drove progress'],
]
const v1 = [
  'End-to-end format optimization',
  'Learning across (Topic × Intent) cells',
  'Six DECIDE intents + "unmapped" handling',
  'Strong-signal reward model',
  'Smart selection with warm-up phase',
  'Content vs format separation',
]
const roadmap = [
  { v: 'V2', t: 'Weak-signal fusion (dwell, scroll, depth)' },
  { v: 'V2', t: 'Content-track learning' },
  { v: 'V2', t: 'Per-user personalization' },
  { v: 'V3', t: 'Thompson Sampling at scale' },
  { v: 'V3', t: 'Cross-cell transfer learning' },
]
const cls = (v: string) => (v.startsWith('+') ? 'pos' : v.startsWith('−') ? 'neg' : 'nul')

const root = ref<HTMLElement | null>(null)
const i = ref(0)
const presenting = ref(false)
const n = slides.length

function next() { i.value = (i.value + 1) % n }
function prev() { i.value = (i.value - 1 + n) % n }
function go(k: number) { i.value = k }
function close() { if (document.fullscreenElement) document.exitFullscreen().catch(() => {}); emit('close') }

async function togglePresent() {
  try {
    if (!document.fullscreenElement) await root.value?.requestFullscreen()
    else await document.exitFullscreen()
  } catch { /* fullscreen may be blocked; ignore */ }
}
function onFsChange() { presenting.value = !!document.fullscreenElement }

function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') { e.preventDefault(); next() }
  else if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); prev() }
  else if (e.key === 'Escape' && !document.fullscreenElement) { e.preventDefault(); close() }
  else if (e.key === 'Home') i.value = 0
  else if (e.key === 'End') i.value = n - 1
}

onMounted(() => {
  document.addEventListener('keydown', onKey)
  document.addEventListener('fullscreenchange', onFsChange)
  root.value?.focus()
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKey)
  document.removeEventListener('fullscreenchange', onFsChange)
})
</script>

<style scoped>
.deck {
  position: fixed; inset: 0; z-index: 200;
  display: flex; flex-direction: column;
  background:
    radial-gradient(80% 60% at 78% 8%, rgba(255, 6, 10, 0.12), transparent 60%),
    radial-gradient(60% 50% at 10% 90%, rgba(255, 6, 10, 0.07), transparent 60%),
    #060608;
  color: #fff; outline: none;
}
.deck:fullscreen { padding: 0; }

/* top bar */
.deck-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); }
.deck-brand { display: inline-flex; align-items: center; gap: 8px; min-width: 0; white-space: nowrap; font: 600 12px/1 'JetBrains Mono', monospace; letter-spacing: 0.04em; color: rgba(255, 255, 255, 0.7); }
.deck-brand .dot { width: 7px; height: 7px; border-radius: 999px; flex: none; background: #ff060a; box-shadow: 0 0 10px 1px rgba(255, 6, 10, 0.7); }
.deck-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.deck-count { font: 600 12px/1 'JetBrains Mono', monospace; color: rgba(255, 255, 255, 0.6); margin-right: 4px; }
.dbtn { display: inline-flex; align-items: center; gap: 6px; height: 34px; min-width: 34px; padding: 0 9px; border-radius: 9px; border: 1px solid rgba(255, 255, 255, 0.14); background: rgba(255, 255, 255, 0.04); color: #fff; cursor: pointer; transition: all 0.15s ease; }
.dbtn:hover { background: rgba(255, 255, 255, 0.1); border-color: rgba(255, 255, 255, 0.28); }
.dbtn svg { width: 17px; height: 17px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.dbtn-label { font-size: 12px; font-weight: 600; }
.dbtn-accent { background: linear-gradient(180deg, #ff2b30, #c20007); border-color: rgba(255, 140, 142, 0.5); }
.dbtn-accent:hover { filter: brightness(1.08); }

/* stage */
.deck-stagewrap { flex: 1; min-height: 0; display: grid; place-items: center; padding: 18px; }
.stage {
  container-type: size;
  width: min(94vw, calc(84vh * 16 / 9)); aspect-ratio: 16 / 9;
  border-radius: 18px; border: 1px solid rgba(255, 255, 255, 0.08);
  background: linear-gradient(160deg, #101013 0%, #0a0a0c 60%, #08080a 100%);
  box-shadow: 0 30px 80px -30px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  overflow: hidden; position: relative;
}
.deck:fullscreen .stage { width: min(99vw, calc(99vh * 16 / 9)); }

.slide-host { position: absolute; inset: 0; }
.slide { position: absolute; inset: 0; padding: 6cqh 7cqw; display: flex; flex-direction: column; }
.slide-center { align-items: center; justify-content: center; text-align: center; gap: 2.4cqh; }
.ey { font: 600 1.7cqw/1 'JetBrains Mono', monospace; letter-spacing: 0.16em; text-transform: uppercase; color: #ff5c60; }
.s-head { margin-bottom: 3.4cqh; }
.s-head h2 { margin-top: 1.2cqh; }
h1 { font-size: 8.2cqw; font-weight: 700; line-height: 1.02; letter-spacing: -0.03em; }
h2 { font-size: 4.2cqw; font-weight: 650; line-height: 1.08; letter-spacing: -0.025em; }
h2.big { font-size: 5.4cqw; }
.hl { color: #ff3b3f; }
.lead { font-size: 2.3cqw; line-height: 1.45; color: rgba(255, 255, 255, 0.66); max-width: 70cqw; }
.slide-center .lead { margin: 0 auto; }
.foot { margin-top: auto; padding-top: 2cqh; font-size: 1.8cqw; color: rgba(255, 255, 255, 0.6); }
.foot b { color: #ff5c60; }

/* title */
.slide-title { align-items: flex-start; justify-content: center; gap: 2.2cqh; }
.kicker { font: 600 1.7cqw/1 'JetBrains Mono', monospace; letter-spacing: 0.16em; color: rgba(255, 255, 255, 0.5); }
.title-orbs { display: flex; gap: 1.4cqw; margin-top: 1cqh; }
.title-orbs span { width: 2.4cqw; height: 2.4cqw; border-radius: 999px; background: radial-gradient(circle at 35% 30%, #ff5c60, #ff060a 70%); box-shadow: 0 0 3cqw -0.4cqw rgba(255, 6, 10, 0.8); animation: ob 3s ease-in-out infinite; }
.title-orbs span:nth-child(odd) { background: radial-gradient(circle at 35% 30%, #fff, #cfcfe0 70%); box-shadow: 0 0 2cqw -0.4cqw rgba(255, 255, 255, 0.5); }
.title-orbs span:nth-child(2) { animation-delay: -0.4s } .title-orbs span:nth-child(3) { animation-delay: -0.8s } .title-orbs span:nth-child(4) { animation-delay: -1.2s } .title-orbs span:nth-child(5) { animation-delay: -1.6s } .title-orbs span:nth-child(6) { animation-delay: -2s }
@keyframes ob { 0%, 100% { transform: translateY(0) } 50% { transform: translateY(-0.8cqh) } }

.arrow-row { display: flex; align-items: center; gap: 1.6cqw; flex-wrap: wrap; justify-content: center; }
.pill { font: 600 1.9cqw/1 'JetBrains Mono', monospace; padding: 1.3cqh 1.6cqw; border-radius: 999px; border: 1px solid rgba(255, 255, 255, 0.16); }
.pill.on { background: rgba(255, 6, 10, 0.14); border-color: rgba(255, 6, 10, 0.5); color: #ff8a8c; }
.pill.dim { color: rgba(255, 255, 255, 0.55); }
.arr { font-size: 3cqw; color: #ff5c60; }

/* two-column */
.two-col { flex: 1; min-height: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 2.4cqw; }
.persona { border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 1.4cqw; background: rgba(255, 255, 255, 0.025); padding: 3cqh 2.4cqw; display: flex; flex-direction: column; gap: 1.4cqh; }
.p-top { display: flex; align-items: center; gap: 1.2cqw; }
.p-ava { width: 4cqw; height: 4cqw; border-radius: 999px; display: grid; place-items: center; background: linear-gradient(180deg, #ff2b30, #c20007); color: #fff; font-weight: 700; font-size: 2cqw; }
.p-top b { font-size: 2.3cqw; display: block; } .p-top i { font-size: 1.6cqw; color: rgba(255, 255, 255, 0.5); font-style: normal; }
.p-q { font-size: 2cqw; color: rgba(255, 255, 255, 0.85); }
.p-want { font-size: 1.9cqw; color: rgba(255, 255, 255, 0.62); line-height: 1.4; } .p-want b { color: #fff; }
.p-fmt { margin-top: auto; font: 600 1.8cqw/1 'JetBrains Mono', monospace; color: rgba(255, 255, 255, 0.6); } .p-fmt b { color: #ff5c60; }

.insight { border-radius: 1.4cqw; padding: 3cqh 2.4cqw; display: flex; flex-direction: column; gap: 1.4cqh; font-size: 2cqw; line-height: 1.4; }
.insight.neg { border: 1px solid rgba(255, 6, 10, 0.3); background: rgba(255, 6, 10, 0.07); }
.insight.warn { border: 1px solid rgba(245, 166, 35, 0.32); background: rgba(245, 166, 35, 0.06); }
.insight p { color: rgba(255, 255, 255, 0.85); font-style: italic; }
.insight b { color: #fff; }
.tag { align-self: flex-start; font: 700 1.5cqw/1 'JetBrains Mono', monospace; letter-spacing: 0.08em; padding: 1cqh 1.2cqw; border-radius: 0.8cqw; background: rgba(255, 255, 255, 0.08); }
.insight.neg .tag { color: #ff8a8c; } .insight.warn .tag { color: #f5c06a; }
.tag.on { background: rgba(255, 6, 10, 0.16); color: #ff8a8c; }

/* DECIDE grid */
.decide-grid { flex: 1; min-height: 0; display: grid; grid-template-columns: repeat(3, 1fr); grid-template-rows: 1fr 1fr; gap: 1.6cqw; }
.dcard { position: relative; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 1.2cqw; background: rgba(255, 255, 255, 0.025); padding: 2cqh 1.8cqw; display: flex; flex-direction: column; gap: 0.7cqh; overflow: hidden; }
.dletter { position: absolute; right: 1cqw; top: -0.6cqh; font-size: 7cqw; font-weight: 800; color: rgba(255, 6, 10, 0.16); line-height: 1; }
.dcard b { font-size: 2.1cqw; } .dcard i { font-size: 1.6cqw; color: rgba(255, 255, 255, 0.6); font-style: normal; }
.dneeds { margin-top: auto; font: 600 1.4cqw/1.2 'JetBrains Mono', monospace; color: #ff5c60; }

/* loop */
.loop-row { flex: 1; min-height: 0; display: flex; align-items: center; gap: 0.6cqw; }
.lstep { flex: 1; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 1.1cqw; background: rgba(255, 255, 255, 0.025); padding: 2.4cqh 1.2cqw; display: flex; flex-direction: column; gap: 0.8cqh; height: 70%; }
.lnum { width: 3.2cqw; height: 3.2cqw; border-radius: 999px; display: grid; place-items: center; background: rgba(255, 6, 10, 0.14); border: 1px solid rgba(255, 6, 10, 0.4); color: #ff8a8c; font-weight: 700; font-size: 1.7cqw; }
.lstep b { font-size: 2cqw; } .lstep i { font-size: 1.5cqw; color: rgba(255, 255, 255, 0.55); font-style: normal; line-height: 1.35; }
.larr { color: #ff5c60; font-size: 2.4cqw; }

/* format menu */
.menu { flex: 1; min-height: 0; display: flex; flex-direction: column; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 1.2cqw; overflow: hidden; }
.menu-head, .menu-row { display: grid; grid-template-columns: 1.1fr 1fr 1fr 1fr; align-items: center; gap: 1cqw; padding: 0 1.8cqw; }
.menu-head { font: 700 1.4cqw/1 'JetBrains Mono', monospace; letter-spacing: 0.06em; text-transform: uppercase; color: rgba(255, 255, 255, 0.5); background: rgba(255, 255, 255, 0.04); height: 5cqh; }
.menu-row { flex: 1; border-top: 1px solid rgba(255, 255, 255, 0.07); font-size: 1.75cqw; color: rgba(255, 255, 255, 0.8); }
.menu-row .mi { font-weight: 700; color: #fff; }

/* reward ledger */
.ledger { flex: 1; min-height: 0; display: flex; flex-direction: column; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 1.1cqw; overflow: hidden; }
.lrow { display: grid; grid-template-columns: 1.5fr 0.6fr 0.6fr 1.5fr; align-items: center; gap: 1cqw; padding: 0 1.8cqw; flex: 1; border-top: 1px solid rgba(255, 255, 255, 0.07); font-size: 1.7cqw; }
.lrow.lhead { flex: 0 0 auto; height: 4.6cqh; border-top: 0; font: 700 1.3cqw/1 'JetBrains Mono', monospace; letter-spacing: 0.06em; text-transform: uppercase; color: rgba(255, 255, 255, 0.5); background: rgba(255, 255, 255, 0.04); }
.lc { text-align: center; } .lm { color: rgba(255, 255, 255, 0.6); }
.lc b { display: inline-grid; place-items: center; min-width: 3cqw; height: 2.6cqh; padding: 0 0.6cqw; border-radius: 0.6cqw; font: 700 1.6cqw/1 'JetBrains Mono', monospace; }
.lc b.pos { color: #34d399; background: rgba(52, 211, 153, 0.12); border: 1px solid rgba(52, 211, 153, 0.3); }
.lc b.neg { color: #ff5c60; background: rgba(255, 6, 10, 0.1); border: 1px solid rgba(255, 6, 10, 0.3); }
.lc b.nul { color: rgba(255, 255, 255, 0.35); }

/* gauges */
.gauge { border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 1.4cqw; background: rgba(255, 255, 255, 0.025); padding: 3cqh 2.4cqw; display: flex; flex-direction: column; gap: 1.2cqh; }
.gauge.alt { border-color: rgba(255, 6, 10, 0.3); background: rgba(255, 6, 10, 0.06); }
.g-num { font-size: 6cqw; font-weight: 800; letter-spacing: -0.03em; color: #fff; }
.gauge.alt .g-num { color: #ff5c60; }
.gauge b { font: 700 1.8cqw/1 'JetBrains Mono', monospace; letter-spacing: 0.08em; color: rgba(255, 255, 255, 0.8); }
.gauge i { font-size: 1.8cqw; color: rgba(255, 255, 255, 0.55); font-style: normal; line-height: 1.4; }

/* quad */
.quad { flex: 1; min-height: 0; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 1.6cqw; }
.qcard { border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 1.1cqw; background: rgba(255, 255, 255, 0.025); padding: 2.4cqh 2cqw; display: flex; flex-direction: column; gap: 0.9cqh; }
.qcard b { font-size: 2.1cqw; color: #ff8a8c; } .qcard i { font-size: 1.7cqw; color: rgba(255, 255, 255, 0.6); font-style: normal; line-height: 1.4; }

/* metrics */
.metric-hero { display: flex; align-items: center; gap: 2.6cqw; border: 1px solid rgba(255, 6, 10, 0.3); background: rgba(255, 6, 10, 0.07); border-radius: 1.4cqw; padding: 3cqh 2.6cqw; margin-bottom: 2cqh; }
.m-big { font-size: 6.4cqw; font-weight: 800; color: #ff3b3f; letter-spacing: -0.03em; }
.metric-hero b { font-size: 2.4cqw; } .metric-hero i { display: block; font-size: 1.7cqw; color: rgba(255, 255, 255, 0.55); font-style: normal; margin-top: 0.6cqh; }
.metric-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.6cqw; }
.mc { border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 1.1cqw; background: rgba(255, 255, 255, 0.025); padding: 2.2cqh 1.8cqw; font-size: 2cqw; }
.mc i { display: block; font-size: 1.5cqw; color: rgba(255, 255, 255, 0.5); font-style: normal; margin-top: 0.6cqh; }
.mu { color: #ff5c60; font-weight: 800; margin-right: 0.5cqw; }

/* scope */
.scope { border-radius: 1.4cqw; padding: 2.6cqh 2.2cqw; display: flex; flex-direction: column; gap: 1.4cqh; }
.scope.in { border: 1px solid rgba(255, 6, 10, 0.28); background: rgba(255, 6, 10, 0.05); }
.scope.next { border: 1px solid rgba(255, 255, 255, 0.1); background: rgba(255, 255, 255, 0.02); }
.scope ul { list-style: none; display: flex; flex-direction: column; gap: 1.1cqh; }
.scope li { position: relative; padding-left: 2cqw; font-size: 1.75cqw; color: rgba(255, 255, 255, 0.82); line-height: 1.35; }
.scope li::before { content: '›'; position: absolute; left: 0; color: #ff5c60; font-weight: 700; }
.scope.next li b { display: inline-grid; place-items: center; min-width: 2.4cqw; font: 700 1.3cqw/1 'JetBrains Mono', monospace; color: #ff8a8c; }

/* slide transition */
.sfade-enter-active { transition: opacity 0.32s ease, transform 0.32s cubic-bezier(0.16, 1, 0.3, 1); }
.sfade-leave-active { transition: opacity 0.18s ease; }
.sfade-enter-from { opacity: 0; transform: translateX(2%) scale(0.992); }
.sfade-leave-to { opacity: 0; }

/* dots */
.deck-dots { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 12px; border-top: 1px solid rgba(255, 255, 255, 0.08); }
.dot-btn { width: 9px; height: 9px; border-radius: 999px; border: 0; background: rgba(255, 255, 255, 0.22); cursor: pointer; transition: all 0.2s ease; padding: 0; }
.dot-btn:hover { background: rgba(255, 255, 255, 0.45); }
.dot-btn.on { width: 24px; border-radius: 999px; background: #ff060a; box-shadow: 0 0 10px -1px rgba(255, 6, 10, 0.7); }

@media (prefers-reduced-motion: reduce) {
  .title-orbs span { animation: none; }
  .sfade-enter-active, .sfade-leave-active { transition: opacity 0.15s ease; }
  .sfade-enter-from { transform: none; }
}

/* mobile: keep the top bar compact so the controls never wrap */
@media (max-width: 640px) {
  .brand-sub { display: none; }
  .deck-count { display: none; }
  .deck-actions { gap: 6px; }
  .dbtn { padding: 0 7px; }
  .dbtn-label { display: none; }
  .deck-bar { padding: 10px 12px; }
  .deck-stagewrap { padding: 10px; }
}
</style>
