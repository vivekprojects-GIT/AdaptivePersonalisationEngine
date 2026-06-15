<script setup lang="ts">
/** MorphingAnswer — APE's signature visual: ONE real answer to ONE question,
 *  reshaping through prose → table → bullets → chart → one-liner on a loop,
 *  with a "learned for you" cue. It is the product demoing itself.
 *
 *  Deep teal-on-ink card with a subtle 3D float + mouse-parallax tilt and
 *  depth transitions between formats. Bold, ownable teal identity. All motion
 *  is reduced-motion aware (freezes to the table state, no auto-cycle). */
import { onMounted, onUnmounted, ref } from 'vue'

type Fmt = { id: string; label: string }
const formats: Fmt[] = [
  { id: 'prose',   label: 'prose' },
  { id: 'table',   label: 'comparison table' },
  { id: 'bullets', label: 'bullet summary' },
  { id: 'chart',   label: 'bar chart' },
  { id: 'oneline', label: 'one-liner' },
]
const idx = ref(1) // start on the table — reads clearly in a static frame
let timer: ReturnType<typeof setInterval> | null = null
let reduce = false

// mouse-parallax tilt
const scene = ref<HTMLDivElement | null>(null)
const tilt = ref({ rx: 3, ry: -7 })
function onMove(e: MouseEvent) {
  if (reduce || !scene.value) return
  const r = scene.value.getBoundingClientRect()
  const px = (e.clientX - r.left) / r.width - 0.5
  const py = (e.clientY - r.top) / r.height - 0.5
  tilt.value = { rx: +( -py * 6 + 3).toFixed(2), ry: +(px * 10 - 7).toFixed(2) }
}
function onLeave() { tilt.value = { rx: 3, ry: -7 } }

onMounted(() => {
  reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduce) return
  timer = setInterval(() => { idx.value = (idx.value + 1) % formats.length }, 2800)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="scene" ref="scene" @mousemove="onMove" @mouseleave="onLeave">
    <div class="glow" aria-hidden="true"></div>

    <div class="card" :style="{ transform: `rotateX(${tilt.rx}deg) rotateY(${tilt.ry}deg)` }">
      <!-- the question (always the same) -->
      <div class="q">
        <span class="who">YOU</span>
        Roth or Traditional IRA, which should I pick?
      </div>

      <!-- answer header: format chip morphs in sync -->
      <div class="ahead">
        <span class="dot"></span>
        <span class="assistant">APE</span>
        <Transition name="chip" mode="out-in">
          <span class="chip" :key="idx">{{ formats[idx].label }}</span>
        </Transition>
      </div>

      <!-- the answer body — same answer, different shape -->
      <div class="body">
        <Transition name="morph" mode="out-in">
          <!-- PROSE -->
          <div v-if="formats[idx].id === 'prose'" key="prose" class="prose">
            If your income will rise, the <b>Roth</b> usually wins. You pay tax
            now at a lower rate and withdraw <b>tax-free</b> later. A Traditional
            just defers the tax instead.
          </div>

          <!-- TABLE -->
          <table v-else-if="formats[idx].id === 'table'" key="table" class="tbl">
            <thead><tr><th></th><th>Roth</th><th>Traditional</th></tr></thead>
            <tbody>
              <tr><td>Tax now</td><td class="hi">Paid</td><td>Deferred</td></tr>
              <tr><td>Withdrawals</td><td class="hi">Tax-free</td><td>Taxed</td></tr>
            </tbody>
          </table>

          <!-- BULLETS -->
          <ul v-else-if="formats[idx].id === 'bullets'" key="bullets" class="bul">
            <li><span class="b"></span>Roth: pay tax now, grow <b>tax-free</b></li>
            <li><span class="b"></span>Traditional: deduct now, taxed later</li>
            <li><span class="b"></span>Under the 24% bracket → Roth wins</li>
          </ul>

          <!-- CHART -->
          <div v-else-if="formats[idx].id === 'chart'" key="chart" class="chart">
            <div class="bars">
              <div class="bar"><div class="fill" style="height:86%"></div><span>Roth</span></div>
              <div class="bar"><div class="fill dim" style="height:62%"></div><span>Trad</span></div>
            </div>
            <div class="cap">after-tax value at 65</div>
          </div>

          <!-- ONE-LINER -->
          <div v-else key="oneline" class="oneline">
            “At 29 with rising income, the <b>Roth</b> almost always wins.”
          </div>
        </Transition>
      </div>

      <!-- learning footer -->
      <div class="foot">
        <div class="dots">
          <span v-for="(f, i) in formats" :key="f.id" class="d" :class="{ on: i === idx }"></span>
        </div>
        <span class="learn">same answer · <b>your shape</b></span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scene {
  position: relative;
  width: 100%;
  perspective: 1200px;
}
.glow {
  position: absolute;
  inset: -8% -6% -12% -6%;
  background: radial-gradient(60% 60% at 60% 28%, rgba(20, 184, 166, 0.12), transparent 72%);
  filter: blur(34px);
  opacity: 0.8;
  z-index: 0;
}
.card {
  position: relative;
  z-index: 1;
  border-radius: 18px;
  padding: 16px 16px 12px;
  color: #1c1c17;
  background: #ffffff;
  border: 1px solid rgba(28, 28, 23, 0.08);
  box-shadow:
    0 30px 60px -28px rgba(28, 28, 23, 0.30),
    0 2px 8px -2px rgba(28, 28, 23, 0.05);
  transform-style: preserve-3d;
  transition: transform 240ms cubic-bezier(0.22, 1, 0.36, 1);
  animation: float 7s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { translate: 0 0; }
  50% { translate: 0 -7px; }
}

/* question */
.q {
  font-size: 12.5px;
  line-height: 1.5;
  color: #3a3a32;
  background: #f4f4ec;
  border: 1px solid rgba(28, 28, 23, 0.06);
  border-radius: 12px;
  padding: 9px 11px;
  transform: translateZ(20px);
}
.who {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #a16207;
  margin-right: 7px;
  vertical-align: middle;
}

/* answer header */
.ahead {
  display: flex;
  align-items: center;
  gap: 7px;
  margin: 12px 2px 8px;
  transform: translateZ(28px);
}
.dot { width: 6px; height: 6px; border-radius: 50%; background: #eab308; box-shadow: 0 0 8px rgba(20,184,166,0.5); }
.assistant { font-size: 10px; font-weight: 600; letter-spacing: 0.04em; color: #57574e; }
.chip {
  font-size: 10.5px;
  font-weight: 600;
  color: #1c1c17;
  background: linear-gradient(180deg, #facc15, #eab308);
  border-radius: 999px;
  padding: 3px 10px;
  box-shadow: 0 4px 12px -5px rgba(13, 148, 136, 0.5);
}

/* body — fixed height so morphs don't jump the layout */
.body {
  position: relative;
  min-height: 116px;
  transform: translateZ(36px);
}

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
.bar .fill.dim { background: linear-gradient(180deg, #cfe9e3, #a7d4cc); }
.bar span { font-size: 10px; color: #7a7a70; }
.cap { font-size: 10px; color: #9a9a90; text-align: center; }

.oneline { font-size: 15px; line-height: 1.5; color: #1c1c17; font-weight: 500; padding-top: 14px; }

/* footer */
.foot {
  display: flex; align-items: center; gap: 10px;
  margin-top: 12px; padding-top: 10px;
  border-top: 1px solid rgba(28, 28, 23, 0.07);
  transform: translateZ(20px);
}
.dots { display: flex; gap: 5px; }
.d { width: 6px; height: 6px; border-radius: 999px; background: rgba(28, 28, 23, 0.15); transition: all 0.5s; }
.d.on { width: 18px; background: #eab308; }
.learn { margin-left: auto; font-size: 9px; text-transform: uppercase; letter-spacing: 0.12em; color: #7a7a70; }
.learn b { color: #a16207; }

/* transitions: depth morph between formats */
.morph-enter-active, .morph-leave-active {
  transition: opacity 420ms cubic-bezier(0.22, 1, 0.36, 1), transform 420ms cubic-bezier(0.22, 1, 0.36, 1);
}
.morph-enter-from { opacity: 0; transform: translateY(14px) translateZ(-30px) rotateX(8deg); }
.morph-leave-to  { opacity: 0; transform: translateY(-14px) translateZ(-30px) rotateX(-8deg); }

.chip-enter-active, .chip-leave-active { transition: opacity 220ms ease, transform 220ms ease; }
.chip-enter-from { opacity: 0; transform: translateY(5px); }
.chip-leave-to   { opacity: 0; transform: translateY(-5px); }

@media (prefers-reduced-motion: reduce) {
  .card { animation: none; }
}
</style>
