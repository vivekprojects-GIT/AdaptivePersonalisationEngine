<!--
  HeroCollage — Ramp-style floating-card composition that LIVES with the demo
  AND tilts in 3D toward the cursor. One clock drives the central MorphingAnswer
  and the surrounding engine cards (classify → select → render → apply), so the
  whole hero changes in lockstep with each question/response. Each card sits at a
  different depth (translateZ); moving the pointer tilts the whole scene so near
  cards parallax more than far ones — a real 3D feel.
-->
<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import MorphingAnswer from './MorphingAnswer.vue'
import { personas, ARMS, INTENTS, CYCLE_MS } from './heroPersonas'

const idx = ref(0)
const p = computed(() => personas[idx.value])
let timer: ReturnType<typeof setInterval> | null = null

const BASE: Record<string, number> = { table: 58, chart: 50, bullets: 43, oneline: 36, prose: 40 }
const armWidth = (key: string) => (key === p.value.fmt ? 92 : BASE[key])
const confidence = computed(() => 62 + (idx.value % 5) * 7)

// --- 3D parallax: tilt the whole scene toward the pointer ---
const scene = ref<HTMLElement | null>(null)
const tilt = ref({ rx: 0, ry: 0 })
let reduce = false
function onParallax(e: PointerEvent) {
  if (reduce || !scene.value) return
  const r = scene.value.getBoundingClientRect()
  const px = (e.clientX - r.left) / r.width - 0.5
  const py = (e.clientY - r.top) / r.height - 0.5
  tilt.value = { rx: +(-py * 9).toFixed(2), ry: +(px * 12).toFixed(2) }
}
function onLeave() { tilt.value = { rx: 0, ry: 0 } }

onMounted(() => {
  reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduce) return
  timer = setInterval(() => { idx.value = (idx.value + 1) % personas.length }, CYCLE_MS)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="collage" @pointermove="onParallax" @pointerleave="onLeave">
    <div class="scene" ref="scene" :style="{ transform: `rotateX(${tilt.rx}deg) rotateY(${tilt.ry}deg)` }">
      <!-- central product card — driven by the same clock -->
      <div class="center" style="--z: 0px"><MorphingAnswer :active-index="idx" /></div>

      <!-- A · classifying intent -->
      <div class="chip-card cc-a" style="--delay: 0.18s; --float: 7s; --z: 72px">
        <div class="cc-head">classifying intent</div>
        <div class="cc-tags">
          <span v-for="it in INTENTS" :key="it" class="t" :class="{ on: it === p.intent }">{{ it }}</span>
        </div>
        <div class="bar"><i :style="{ width: confidence + '%' }"></i></div>
        <span class="handles" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
      </div>

      <!-- B · selecting format · UCB -->
      <div class="chip-card cc-b" style="--delay: 0.3s; --float: 8.4s; --z: 118px">
        <div class="cc-head">selecting format · ucb</div>
        <div class="arms">
          <div v-for="arm in ARMS" :key="arm.key" class="arm" :class="{ on: arm.key === p.fmt }">
            <span>{{ arm.label }}</span>
            <div class="ab"><i :style="{ width: armWidth(arm.key) + '%' }"></i></div>
          </div>
        </div>
        <span class="handles" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
      </div>

      <!-- C · rendering -->
      <div class="chip-card cc-c" style="--delay: 0.42s; --float: 7.6s; --z: 46px">
        <div class="cc-head">rendering ·
          <Transition name="swap" mode="out-in"><b :key="p.fmt" class="fmt">{{ p.fmt }}</b></Transition>
        </div>
        <div class="lines">
          <span></span><span></span><span style="width: 68%"></span><span style="width: 84%"></span>
        </div>
      </div>

      <!-- D · applied + reward → this person -->
      <div class="chip-card cc-d" style="--delay: 0.54s; --float: 9s; --z: 96px">
        <Transition name="swap" mode="out-in">
          <div class="cc-mini" :key="idx">
            <span class="ava">{{ p.initial }}</span>
            <div>
              <div class="cc-head">applied · <b>+{{ p.reward.toFixed(2) }}</b></div>
              <div class="cc-sub">{{ p.label }} → {{ p.name }}</div>
            </div>
          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>

<style scoped>
.collage { position: relative; width: 100%; padding: 30px 8px 24px; perspective: 1300px; }
.scene {
  position: relative; width: 100%;
  transform-style: preserve-3d;
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: transform;
}
.center { position: relative; z-index: 20; max-width: 360px; margin: 0 auto; transform: translateZ(var(--z)); }

/* ---- floating status cards (each at its own depth) ---- */
.chip-card {
  position: absolute;
  width: 172px;
  padding: 11px 12px;
  background: color-mix(in oklab, var(--card) 92%, #fff 0%);
  border: 1px solid var(--border);
  border-radius: 11px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3), 0 20px 44px -18px rgba(0, 0, 0, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  transform: translateZ(var(--z));
  transform-style: preserve-3d;
  animation:
    cardIn3d 0.7s cubic-bezier(0.16, 1, 0.3, 1) var(--delay) both,
    cardFloat3d var(--float) ease-in-out calc(var(--delay) + 0.7s) infinite;
  will-change: transform;
}
.cc-a { top: 2%;  left: -7%;  z-index: 10; }
.cc-b { top: 12%; right: -9%; z-index: 30; }
.cc-c { bottom: 13%; left: -8%; z-index: 10; }
.cc-d { bottom: 0%;  right: 0%;  z-index: 30; width: 196px; }

.cc-head {
  font: 600 9.5px/1.1 'JetBrains Mono', ui-monospace, monospace;
  letter-spacing: 0.07em; text-transform: uppercase; color: var(--muted-foreground);
}
.cc-head b { color: var(--foreground); }
.fmt { display: inline-block; color: var(--foreground); }

.cc-tags { display: flex; gap: 5px; margin-top: 9px; }
.t {
  font-size: 10px; font-weight: 500; padding: 2px 7px; border-radius: 999px;
  background: var(--secondary); color: var(--muted-foreground); border: 1px solid var(--border);
  transition: background 0.4s ease, color 0.4s ease, border-color 0.4s ease;
}
.t.on { background: var(--accent); color: var(--accent-foreground); border-color: transparent; }

.bar { margin-top: 9px; height: 4px; border-radius: 999px; background: var(--secondary); overflow: hidden; }
.bar i { display: block; height: 100%; background: var(--foreground); border-radius: 999px;
  transition: width 0.55s cubic-bezier(0.16, 1, 0.3, 1); }

.arms { margin-top: 9px; display: flex; flex-direction: column; gap: 5px; }
.arm { display: flex; align-items: center; gap: 8px; }
.arm span {
  width: 46px; flex: none; font: 500 10px/1 'JetBrains Mono', ui-monospace, monospace;
  color: var(--muted-foreground); transition: color 0.4s ease;
}
.arm.on span { color: var(--foreground); }
.ab { flex: 1; height: 5px; border-radius: 999px; background: var(--secondary); overflow: hidden; }
.ab i { display: block; height: 100%; border-radius: 999px; background: var(--border);
  transition: width 0.55s cubic-bezier(0.16, 1, 0.3, 1), background 0.4s ease; }
.arm.on .ab i { background: var(--accent); }

.lines { margin-top: 9px; display: flex; flex-direction: column; gap: 6px; }
.lines span { display: block; height: 6px; width: 100%; border-radius: 3px; background: var(--secondary); }

.cc-mini { display: flex; align-items: center; gap: 9px; }
.ava {
  width: 26px; height: 26px; flex: none; display: grid; place-items: center;
  border-radius: 999px; background: var(--accent); color: var(--accent-foreground);
  font: 600 11px/1 'Geist', sans-serif;
}
.cc-sub { margin-top: 3px; font-size: 11px; color: var(--muted-foreground); }

.handles i { position: absolute; width: 5px; height: 5px; background: var(--accent); border-radius: 1px; }
.handles i:nth-child(1) { top: -3px; left: -3px; }
.handles i:nth-child(2) { top: -3px; right: -3px; }
.handles i:nth-child(3) { bottom: -3px; left: -3px; }
.handles i:nth-child(4) { bottom: -3px; right: -3px; }

.swap-enter-active, .swap-leave-active { transition: opacity 0.3s ease, transform 0.3s ease; }
.swap-enter-from { opacity: 0; transform: translateY(5px); }
.swap-leave-to   { opacity: 0; transform: translateY(-5px); }

/* 3D entrance: fly up + untilt from below, holding the card's depth. */
@keyframes cardIn3d {
  from { opacity: 0; transform: translateZ(var(--z)) translateY(22px) rotateX(-14deg) scale(0.95); }
  to   { opacity: 1; transform: translateZ(var(--z)) translateY(0) rotateX(0) scale(1); }
}
/* float + a hair of roll, keeping depth so parallax still reads */
@keyframes cardFloat3d {
  0%, 100% { transform: translateZ(var(--z)) translateY(0) rotateZ(0deg); }
  50%      { transform: translateZ(var(--z)) translateY(-7px) rotateZ(0.6deg); }
}

@media (max-width: 1024px) { .chip-card { display: none; } .center { max-width: 440px; } }
@media (prefers-reduced-motion: reduce) {
  .scene { transition: none; }
  .chip-card { animation: cardIn3d 0.4s ease both; }
}
</style>
