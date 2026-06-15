<script setup lang="ts">
/** MorphingAnswer — APE's product demo, auto-playing like a short hero video:
 *  the SAME question, asked by different people, answered in each person's
 *  preferred format. A light card with a "live" bar and a "for <name>" header
 *  that morphs through table / one-liner / bullets / chart / prose. Subtle 3D
 *  tilt; reduced-motion freezes on the first persona. */
import { computed, onMounted, onUnmounted, ref } from 'vue'

type Persona = { name: string; initial: string; fmt: string; label: string; note: string }
const personas: Persona[] = [
  { name: 'Priya',  initial: 'P', fmt: 'table',   label: 'comparison table', note: 'reads the full breakdown' },
  { name: 'Marcus', initial: 'M', fmt: 'oneline', label: 'one-liner',        note: 'just wants the verdict' },
  { name: 'Dana',   initial: 'D', fmt: 'bullets', label: 'bullet summary',   note: 'skims the key points' },
  { name: 'Sam',    initial: 'S', fmt: 'chart',   label: 'bar chart',        note: 'thinks in visuals' },
  { name: 'Alex',   initial: 'A', fmt: 'prose',   label: 'short paragraph',  note: 'likes the full story' },
]
const idx = ref(0)
const p = computed(() => personas[idx.value])
let timer: ReturnType<typeof setInterval> | null = null
let reduce = false

const scene = ref<HTMLDivElement | null>(null)
const tilt = ref({ rx: 2, ry: -4 })
function onMove(e: MouseEvent) {
  if (reduce || !scene.value) return
  const r = scene.value.getBoundingClientRect()
  const px = (e.clientX - r.left) / r.width - 0.5
  const py = (e.clientY - r.top) / r.height - 0.5
  tilt.value = { rx: +(-py * 4 + 2).toFixed(2), ry: +(px * 7 - 4).toFixed(2) }
}
function onLeave() { tilt.value = { rx: 2, ry: -4 } }

onMounted(() => {
  reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduce) return
  timer = setInterval(() => { idx.value = (idx.value + 1) % personas.length }, 2900)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="scene" ref="scene" @mousemove="onMove" @mouseleave="onLeave">
    <div class="glow" aria-hidden="true"></div>

    <div class="card" :style="{ transform: `rotateX(${tilt.rx}deg) rotateY(${tilt.ry}deg)` }">
      <!-- live demo bar -->
      <div class="demo-bar">
        <span class="live-dot"></span>
        live · one question, every person
      </div>

      <!-- the question (always the same) -->
      <div class="q">
        <span class="who">ASKED</span>
        Roth or Traditional IRA, which should I pick?
      </div>

      <!-- who APE is answering + the format it picked for them -->
      <div class="ahead">
        <Transition name="chip" mode="out-in">
          <div class="who-row" :key="idx">
            <span class="avatar">{{ p.initial }}</span>
            <div class="meta">
              <div class="pname">for {{ p.name }}</div>
              <div class="pnote">{{ p.note }}</div>
            </div>
          </div>
        </Transition>
        <Transition name="chip" mode="out-in">
          <span class="chip" :key="'c' + idx">{{ p.label }}</span>
        </Transition>
      </div>

      <!-- the answer body — same answer, that person's shape -->
      <div class="body">
        <Transition name="morph" mode="out-in">
          <div v-if="p.fmt === 'prose'" key="prose" class="prose">
            If your income will rise, the <b>Roth</b> usually wins. You pay tax now at a lower
            rate and withdraw <b>tax-free</b> later. A Traditional just defers the tax instead.
          </div>

          <table v-else-if="p.fmt === 'table'" key="table" class="tbl">
            <thead><tr><th></th><th>Roth</th><th>Traditional</th></tr></thead>
            <tbody>
              <tr><td>Tax now</td><td class="hi">Paid</td><td>Deferred</td></tr>
              <tr><td>Withdrawals</td><td class="hi">Tax-free</td><td>Taxed</td></tr>
            </tbody>
          </table>

          <ul v-else-if="p.fmt === 'bullets'" key="bullets" class="bul">
            <li><span class="b"></span>Roth: pay tax now, grow <b>tax-free</b></li>
            <li><span class="b"></span>Traditional: deduct now, taxed later</li>
            <li><span class="b"></span>Under the 24% bracket, Roth wins</li>
          </ul>

          <div v-else-if="p.fmt === 'chart'" key="chart" class="chart">
            <div class="bars">
              <div class="bar"><div class="fill" style="height:86%"></div><span>Roth</span></div>
              <div class="bar"><div class="fill dim" style="height:62%"></div><span>Trad</span></div>
            </div>
            <div class="cap">after-tax value at 65</div>
          </div>

          <div v-else key="oneline" class="oneline">
            “At 29 with rising income, the <b>Roth</b> almost always wins.”
          </div>
        </Transition>
      </div>

      <!-- footer -->
      <div class="foot">
        <div class="dots">
          <span v-for="(pp, i) in personas" :key="pp.name" class="d" :class="{ on: i === idx }"></span>
        </div>
        <span class="learn">same answer · <b>{{ p.name }}’s shape</b></span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scene { position: relative; width: 100%; perspective: 1200px; }
.glow {
  position: absolute; inset: -8% -6% -12% -6%;
  background: radial-gradient(60% 60% at 60% 28%, rgba(234, 179, 8, 0.16), transparent 72%);
  filter: blur(34px); opacity: 0.8; z-index: 0;
}
.card {
  position: relative; z-index: 1; border-radius: 18px; padding: 0 0 12px;
  color: #1c1c17; background: #ffffff; overflow: hidden;
  border: 1px solid rgba(28, 28, 23, 0.08);
  box-shadow: 0 30px 60px -28px rgba(28, 28, 23, 0.30), 0 2px 8px -2px rgba(28, 28, 23, 0.05);
  transform-style: preserve-3d;
  transition: transform 240ms cubic-bezier(0.22, 1, 0.36, 1);
  animation: float 7s ease-in-out infinite;
}
@keyframes float { 0%, 100% { translate: 0 0; } 50% { translate: 0 -7px; } }

/* live demo bar */
.demo-bar {
  display: flex; align-items: center; gap: 8px;
  padding: 9px 14px; font-size: 10px; font-weight: 600; letter-spacing: 0.1em;
  text-transform: uppercase; color: #7a7a70;
  background: #faf9f3; border-bottom: 1px solid rgba(28, 28, 23, 0.07);
}
.live-dot {
  width: 7px; height: 7px; border-radius: 50%; background: #eab308;
  box-shadow: 0 0 0 0 rgba(234, 179, 8, 0.5); animation: pulse 2s ease-out infinite;
}
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(234, 179, 8, 0.5); }
  70% { box-shadow: 0 0 0 7px rgba(234, 179, 8, 0); }
  100% { box-shadow: 0 0 0 0 rgba(234, 179, 8, 0); }
}

.q {
  margin: 14px 16px 0; font-size: 12.5px; line-height: 1.5; color: #3a3a32;
  background: #f4f4ec; border: 1px solid rgba(28, 28, 23, 0.06);
  border-radius: 12px; padding: 9px 11px;
}
.who { font-size: 9px; font-weight: 700; letter-spacing: 0.12em; color: #a16207; margin-right: 7px; vertical-align: middle; }

.ahead { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin: 13px 16px 9px; }
.who-row { display: flex; align-items: center; gap: 9px; }
.avatar {
  width: 30px; height: 30px; border-radius: 9px; flex: none;
  background: linear-gradient(180deg, #facc15, #eab308); color: #1c1c17;
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 13px;
}
.meta { line-height: 1.25; }
.pname { font-size: 12.5px; font-weight: 600; color: #1c1c17; }
.pnote { font-size: 10.5px; color: #7a7a70; }
.chip {
  flex: none; font-size: 10.5px; font-weight: 600; color: #1c1c17;
  background: linear-gradient(180deg, #facc15, #eab308); border-radius: 999px; padding: 3px 10px;
  box-shadow: 0 4px 12px -5px rgba(234, 179, 8, 0.6);
}

.body { position: relative; min-height: 116px; margin: 0 16px; }
.prose { font-size: 13px; line-height: 1.6; color: #3a3a32; }
.prose b, .bul b, .oneline b { color: #a16207; font-weight: 700; }
.tbl { width: 100%; border-collapse: collapse; font-size: 12px; }
.tbl th { text-align: left; font-weight: 600; color: #7a7a70; padding: 4px 6px; font-size: 10.5px; }
.tbl td { padding: 6px 6px; border-top: 1px solid rgba(28, 28, 23, 0.07); color: #3a3a32; }
.tbl td:first-child { color: #57574e; }
.tbl .hi { color: #a16207; font-weight: 600; }
.bul { list-style: none; margin: 0; padding: 2px 0; display: grid; gap: 9px; font-size: 12.5px; color: #3a3a32; }
.bul li { display: flex; align-items: center; gap: 9px; }
.bul .b { width: 6px; height: 6px; border-radius: 2px; background: #eab308; flex: none; }
.chart { display: flex; flex-direction: column; gap: 8px; padding-top: 4px; }
.bars { display: flex; align-items: flex-end; gap: 18px; height: 86px; padding: 0 6px; }
.bar { display: flex; flex-direction: column; align-items: center; gap: 6px; width: 46px; height: 100%; justify-content: flex-end; }
.bar .fill { width: 100%; border-radius: 6px 6px 3px 3px; background: linear-gradient(180deg, #facc15, #a16207); }
.bar .fill.dim { background: linear-gradient(180deg, #f0e6c0, #d9cba0); }
.bar span { font-size: 10px; color: #7a7a70; }
.cap { font-size: 10px; color: #9a9a90; text-align: center; }
.oneline { font-size: 15px; line-height: 1.5; color: #1c1c17; font-weight: 500; padding-top: 14px; }

.foot {
  display: flex; align-items: center; gap: 10px; margin: 12px 16px 0; padding-top: 10px;
  border-top: 1px solid rgba(28, 28, 23, 0.07);
}
.dots { display: flex; gap: 5px; }
.d { width: 6px; height: 6px; border-radius: 999px; background: rgba(28, 28, 23, 0.15); transition: all 0.5s; }
.d.on { width: 18px; background: #eab308; }
.learn { margin-left: auto; font-size: 9px; text-transform: uppercase; letter-spacing: 0.1em; color: #7a7a70; }
.learn b { color: #a16207; }

.morph-enter-active, .morph-leave-active {
  transition: opacity 420ms cubic-bezier(0.22, 1, 0.36, 1), transform 420ms cubic-bezier(0.22, 1, 0.36, 1);
}
.morph-enter-from { opacity: 0; transform: translateY(12px); }
.morph-leave-to  { opacity: 0; transform: translateY(-12px); }
.chip-enter-active, .chip-leave-active { transition: opacity 240ms ease, transform 240ms ease; }
.chip-enter-from { opacity: 0; transform: translateY(5px); }
.chip-leave-to   { opacity: 0; transform: translateY(-5px); }

@media (prefers-reduced-motion: reduce) { .card { animation: none; } .live-dot { animation: none; } }
</style>
