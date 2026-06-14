<script setup lang="ts">
/** VizChart, animated SVG charts, now FULLY INTERACTIVE: every kind tracks
 *  the pointer and shows a live value tooltip (bars, lines, area, donut,
 *  heatmap, 3D bars, bubbles), so nothing on the page reads as a static
 *  image. Pure SVG + Vue, theme-aware, reduced-motion safe.
 */
import { ref } from 'vue'

const props = defineProps<{ kind: 'bars' | 'area' | 'donut' | 'iso' | 'radar' | 'bubbles' | 'lines' | 'heat' }>()

// Cohesive cool palette led by the theme violet, with one warm accent.
const CYAN = '#22d3ee'
const TEAL = '#2dd4bf'
const VIOLET = '#0d9488'
const BLUE = '#0f766e'
const EMERALD = '#34d399'
const AMBER = '#fb7185'

/* ---- shared hover tooltip ---- */
const tip = ref<{ x: number; y: number; head: string; rows: { c: string; t: string }[] } | null>(null)
const hotIdx = ref<number | null>(null)

function svgPoint(e: PointerEvent, vw: number, vh: number) {
  const el = e.currentTarget as SVGSVGElement
  const r = el.getBoundingClientRect()
  return {
    x: ((e.clientX - r.left) / r.width) * vw,
    y: ((e.clientY - r.top) / r.height) * vh,
    px: e.clientX - r.left,
    py: e.clientY - r.top,
    w: r.width,
  }
}
function placeTip(p: { px: number; py: number; w: number }, head: string, rows: { c: string; t: string }[]) {
  tip.value = { x: Math.min(Math.max(p.px, 60), p.w - 60), y: Math.max(p.py - 14, 8), head, rows }
}
function clearTip() {
  tip.value = null
  hotIdx.value = null
}

/* ---- bars ---- */
const bars = [42, 68, 55, 88, 74, 96, 61]
const barLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
function onBars(e: PointerEvent) {
  const p = svgPoint(e, 200, 120)
  const i = Math.max(0, Math.min(6, Math.round((p.x - 22) / 26)))
  hotIdx.value = i
  placeTip(p, barLabels[i], [{ c: VIOLET, t: `${bars[i]} answers` }])
}

/* ---- area ---- */
const areaLine = 'M0,86 C24,80 40,52 64,58 C88,64 104,30 128,34 C152,38 170,14 200,20'
const areaFill = `${areaLine} L200,110 L0,110 Z`
const areaDots = [
  { x: 0, y: 86, v: 24 }, { x: 64, y: 58, v: 52 }, { x: 128, y: 34, v: 76 }, { x: 200, y: 20, v: 90 },
]
function onArea(e: PointerEvent) {
  const p = svgPoint(e, 200, 120)
  let best = 0
  areaDots.forEach((d, i) => { if (Math.abs(d.x - p.x) < Math.abs(areaDots[best].x - p.x)) best = i })
  hotIdx.value = best
  placeTip(p, `Week ${best + 1}`, [{ c: CYAN, t: `index ${areaDots[best].v}` }])
}

/* ---- donut ---- */
const R = 34
const CIRC = 2 * Math.PI * R
const donutSegs = [
  { frac: 0.42, color: CYAN, name: 'Cloud' },
  { frac: 0.27, color: VIOLET, name: 'Devices' },
  { frac: 0.19, color: EMERALD, name: 'Services' },
  { frac: 0.12, color: AMBER, name: 'Other' },
]
let _acc = 0
const donutArcs = donutSegs.map((s, i) => {
  const dash = s.frac * CIRC
  const gap = CIRC - dash
  const offset = -_acc * CIRC
  _acc += s.frac
  return { ...s, dash, gap, offset, delay: i * 0.18 }
})
function onDonut(e: PointerEvent) {
  const p = svgPoint(e, 120, 120)
  const dx = p.x - 60, dy = p.y - 60
  const dist = Math.sqrt(dx * dx + dy * dy)
  if (dist < 22 || dist > 50) return clearTip()
  let ang = Math.atan2(dy, dx) + Math.PI / 2 // 0 at 12 o'clock
  if (ang < 0) ang += Math.PI * 2
  const frac = ang / (Math.PI * 2)
  let acc = 0, seg = 0
  for (let i = 0; i < donutSegs.length; i++) { acc += donutSegs[i].frac; if (frac <= acc) { seg = i; break } }
  hotIdx.value = seg
  placeTip(p, donutSegs[seg].name, [{ c: donutSegs[seg].color, t: `${Math.round(donutSegs[seg].frac * 100)}% share` }])
}

/* ---- iso 3D bars ---- */
const isoHeights = [40, 66, 52, 80, 70]
const isoLabels = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5']
function isoBar(i: number, h: number) {
  const bx = 26 + i * 30, bw = 18, d = 9, baseY = 116
  const topY = baseY - h
  return {
    front: `${bx},${topY} ${bx + bw},${topY} ${bx + bw},${baseY} ${bx},${baseY}`,
    top: `${bx},${topY} ${bx + d},${topY - d} ${bx + bw + d},${topY - d} ${bx + bw},${topY}`,
    side: `${bx + bw},${topY} ${bx + bw + d},${topY - d} ${bx + bw + d},${baseY - d} ${bx + bw},${baseY}`,
    delay: i * 0.12,
  }
}
const isoBars = isoHeights.map((h, i) => isoBar(i, h))
function onIso(e: PointerEvent) {
  const p = svgPoint(e, 200, 130)
  const i = Math.max(0, Math.min(4, Math.round((p.x - 35) / 30)))
  hotIdx.value = i
  placeTip(p, isoLabels[i], [{ c: VIOLET, t: `${isoHeights[i]}K units` }])
}

/* ---- radar ---- */
function radarPt(k: number, val: number, radius = 42) {
  const ang = -Math.PI / 2 + (k * 2 * Math.PI) / 5
  return `${(60 + Math.cos(ang) * radius * val).toFixed(1)},${(60 + Math.sin(ang) * radius * val).toFixed(1)}`
}
const radarRings = [1, 0.66, 0.33].map((r) => [0, 1, 2, 3, 4].map((k) => radarPt(k, r)).join(' '))
const radarData = [0.9, 0.6, 0.8, 0.5, 0.75]
const radarNames = ['Speed', 'Clarity', 'Depth', 'Brevity', 'Fit']
const radarPoly = [0, 1, 2, 3, 4].map((k) => radarPt(k, radarData[k])).join(' ')
function onRadar(e: PointerEvent) {
  const p = svgPoint(e, 120, 120)
  let best = 0, bd = 1e9
  for (let k = 0; k < 5; k++) {
    const [x, y] = radarPt(k, radarData[k]).split(',').map(Number)
    const d = (x - p.x) ** 2 + (y - p.y) ** 2
    if (d < bd) { bd = d; best = k }
  }
  hotIdx.value = best
  placeTip(p, radarNames[best], [{ c: CYAN, t: `${Math.round(radarData[best] * 100)} / 100` }])
}

/* ---- bubbles ---- */
const bubbles = [
  { x: 40, y: 70, r: 18, c: CYAN, d: 0, n: 'Tables' },
  { x: 95, y: 42, r: 26, c: VIOLET, d: 0.4, n: 'Bullets' },
  { x: 150, y: 78, r: 14, c: EMERALD, d: 0.8, n: 'Steps' },
  { x: 120, y: 30, r: 10, c: TEAL, d: 1.2, n: 'Cards' },
  { x: 70, y: 30, r: 12, c: BLUE, d: 0.6, n: 'Prose' },
  { x: 168, y: 40, r: 16, c: AMBER, d: 1.0, n: 'Charts' },
]
function onBubbles(e: PointerEvent) {
  const p = svgPoint(e, 200, 110)
  let best = -1, bd = 1e9
  bubbles.forEach((b, i) => {
    const d = (b.x - p.x) ** 2 + (b.y - p.y) ** 2
    if (d < bd) { bd = d; best = i }
  })
  if (bd > 1600) return clearTip()
  hotIdx.value = best
  placeTip(p, bubbles[best].n, [{ c: bubbles[best].c, t: `${bubbles[best].r * 4}% engagement` }])
}

/* ---- multi-series time series ---- */
const tsX = [0, 50, 100, 150, 200]
const tsSeries = [
  { d: 'M0,92 C20,88 36,70 56,72 C80,75 96,52 120,50 C146,48 162,30 200,26', c: VIOLET, delay: 0, n: 'tables', v: [18, 38, 55, 70, 84] },
  { d: 'M0,98 C24,96 44,86 66,84 C92,82 110,66 134,64 C160,62 180,52 200,46', c: CYAN, delay: 0.35, n: 'bullets', v: [12, 26, 38, 52, 64] },
  { d: 'M0,104 C28,103 52,98 78,95 C108,91 134,84 200,72', c: EMERALD, delay: 0.7, n: 'steps', v: [6, 14, 22, 30, 38] },
]
const tsGrid = [28, 56, 84]
function onLines(e: PointerEvent) {
  const p = svgPoint(e, 200, 120)
  let best = 0
  tsX.forEach((x, i) => { if (Math.abs(x - p.x) < Math.abs(tsX[best] - p.x)) best = i })
  hotIdx.value = best
  placeTip(p, `T${best + 1}`, tsSeries.map((s) => ({ c: s.c, t: `${s.n} ${s.v[best]}%` })))
}

/* ---- heatmap ---- */
const heatCols = 10
const heatData = [
  2, 4, 6, 5, 3, 2, 1, 2, 3, 2,
  3, 6, 8, 7, 5, 3, 2, 3, 4, 3,
  4, 7, 9, 9, 7, 5, 3, 4, 5, 4,
  3, 5, 8, 9, 8, 6, 4, 5, 6, 4,
  2, 4, 6, 7, 6, 5, 3, 4, 5, 3,
  1, 2, 4, 5, 4, 3, 2, 2, 3, 2,
]
function onHeat(e: PointerEvent) {
  const p = svgPoint(e, 200, 120)
  const c = Math.max(0, Math.min(9, Math.floor((p.x - 4) / 19.5)))
  const r = Math.max(0, Math.min(5, Math.floor((p.y - 8) / 18.5)))
  const i = r * heatCols + c
  hotIdx.value = i
  placeTip(p, `hour ${c + 9}:00 · day ${r + 1}`, [{ c: VIOLET, t: `${heatData[i] * 11} sessions` }])
}
</script>

<template>
  <div class="relative w-full h-full" @pointerleave="clearTip()">

    <!-- BARS -->
    <svg v-if="kind === 'bars'" viewBox="0 0 200 120" class="w-full h-full cursor-crosshair" aria-hidden="true" @pointermove="onBars">
      <defs>
        <linearGradient id="vg-bar" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" :stop-color="CYAN" /><stop offset="100%" :stop-color="VIOLET" />
        </linearGradient>
      </defs>
      <line x1="8" y1="110" x2="196" y2="110" stroke="currentColor" stroke-opacity="0.18" />
      <g v-for="(h, i) in bars" :key="i">
        <rect
          class="viz-bar vz-el"
          :class="{ 'vz-hot': hotIdx === i, 'vz-dim': tip && hotIdx !== i }"
          :x="14 + i * 26" :y="110 - h" width="16" :height="h" rx="3"
          fill="url(#vg-bar)" :style="{ animationDelay: i * 0.08 + 's' }"
        />
      </g>
    </svg>

    <!-- AREA -->
    <svg v-else-if="kind === 'area'" viewBox="0 0 200 120" class="w-full h-full cursor-crosshair" aria-hidden="true" @pointermove="onArea">
      <defs>
        <linearGradient id="vg-area" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" :stop-color="CYAN" stop-opacity="0.45" /><stop offset="100%" :stop-color="CYAN" stop-opacity="0" />
        </linearGradient>
      </defs>
      <path class="viz-area" :d="areaFill" fill="url(#vg-area)" />
      <path class="viz-line" :d="areaLine" fill="none" :stroke="CYAN" stroke-width="2.5" stroke-linecap="round" />
      <circle
        v-for="(p, i) in areaDots" :key="i"
        class="viz-dot vz-el" :class="{ 'vz-hot': hotIdx === i }"
        :cx="p.x" :cy="p.y" :r="hotIdx === i ? 5 : 3.4" :fill="VIOLET"
        :style="{ animationDelay: 1 + i * 0.18 + 's' }"
      />
    </svg>

    <!-- DONUT -->
    <svg v-else-if="kind === 'donut'" viewBox="0 0 120 120" class="w-full h-full cursor-crosshair" aria-hidden="true" @pointermove="onDonut">
      <circle cx="60" cy="60" :r="R" fill="none" stroke="currentColor" stroke-opacity="0.1" stroke-width="14" />
      <circle
        v-for="(a, i) in donutArcs" :key="i"
        class="viz-arc vz-el" :class="{ 'vz-dim': tip && hotIdx !== i }"
        cx="60" cy="60" :r="R" fill="none" :stroke="a.color" :stroke-width="hotIdx === i ? 17 : 14" stroke-linecap="round"
        :stroke-dasharray="`${a.dash} ${a.gap}`"
        :style="{ '--len': CIRC + 'px', '--off': a.offset + 'px', strokeDashoffset: a.offset + 'px', animationDelay: a.delay + 's' }"
      />
      <text x="60" y="58" text-anchor="middle" class="fill-foreground" font-size="17" font-weight="700">
        {{ hotIdx !== null && tip ? Math.round(donutSegs[hotIdx]?.frac * 100) + '%' : '42%' }}
      </text>
      <text x="60" y="74" text-anchor="middle" fill="currentColor" fill-opacity="0.55" font-size="8">
        {{ hotIdx !== null && tip ? donutSegs[hotIdx]?.name.toLowerCase() : 'share' }}
      </text>
    </svg>

    <!-- ISO 3D BARS -->
    <svg v-else-if="kind === 'iso'" viewBox="0 0 200 130" class="w-full h-full cursor-crosshair" aria-hidden="true" @pointermove="onIso">
      <defs>
        <linearGradient id="vg-iso-f" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" :stop-color="CYAN" /><stop offset="100%" :stop-color="BLUE" />
        </linearGradient>
      </defs>
      <polygon points="14,116 110,92 196,116 100,140" fill="currentColor" fill-opacity="0.05" />
      <g
        v-for="(b, i) in isoBars" :key="i"
        class="iso-bar vz-el" :class="{ 'vz-hot': hotIdx === i, 'vz-dim': tip && hotIdx !== i }"
        :style="{ animationDelay: b.delay + 's' }"
      >
        <polygon :points="b.side" :fill="VIOLET" fill-opacity="0.85" />
        <polygon :points="b.front" fill="url(#vg-iso-f)" />
        <polygon :points="b.top" :fill="TEAL" fill-opacity="0.95" />
      </g>
    </svg>

    <!-- RADAR -->
    <svg v-else-if="kind === 'radar'" viewBox="0 0 120 120" class="w-full h-full cursor-crosshair" aria-hidden="true" @pointermove="onRadar">
      <polygon v-for="(ring, i) in radarRings" :key="i" :points="ring" fill="none" stroke="currentColor" stroke-opacity="0.14" />
      <line v-for="k in 5" :key="'a' + k" x1="60" y1="60" :x2="radarPt(k - 1, 1).split(',')[0]" :y2="radarPt(k - 1, 1).split(',')[1]" stroke="currentColor" stroke-opacity="0.12" />
      <polygon class="viz-poly" :points="radarPoly" :fill="CYAN" fill-opacity="0.28" :stroke="CYAN" stroke-width="2" />
      <circle
        v-for="k in 5" :key="'d' + k"
        class="viz-dot vz-el" :class="{ 'vz-hot': hotIdx === k - 1 }"
        :cx="radarPt(k - 1, radarData[k - 1]).split(',')[0]"
        :cy="radarPt(k - 1, radarData[k - 1]).split(',')[1]"
        :r="hotIdx === k - 1 ? 4.2 : 2.6" :fill="VIOLET" :style="{ animationDelay: 0.5 + k * 0.08 + 's' }"
      />
    </svg>

    <!-- BUBBLES -->
    <svg v-else-if="kind === 'bubbles'" viewBox="0 0 200 110" class="w-full h-full cursor-crosshair" aria-hidden="true" @pointermove="onBubbles">
      <defs>
        <radialGradient id="vg-bub" cx="35%" cy="30%" r="70%">
          <stop offset="0%" stop-color="#fff" stop-opacity="0.55" /><stop offset="100%" stop-color="#fff" stop-opacity="0" />
        </radialGradient>
      </defs>
      <g
        v-for="(b, i) in bubbles" :key="i"
        class="viz-bubble vz-el" :class="{ 'vz-hot': hotIdx === i, 'vz-dim': tip && hotIdx !== i }"
        :style="{ animationDelay: b.d + 's' }"
      >
        <circle class="viz-dot" :cx="b.x" :cy="b.y" :r="b.r" :fill="b.c" fill-opacity="0.78" :style="{ animationDelay: b.d * 0.4 + 's' }" />
        <circle :cx="b.x" :cy="b.y" :r="b.r" fill="url(#vg-bub)" />
      </g>
    </svg>

    <!-- MULTI-SERIES LINES -->
    <svg v-else-if="kind === 'lines'" viewBox="0 0 200 120" class="w-full h-full cursor-crosshair" aria-hidden="true" @pointermove="onLines">
      <line v-for="g in tsGrid" :key="g" x1="0" :y1="g" x2="200" :y2="g" stroke="currentColor" stroke-opacity="0.1" />
      <line x1="0" y1="112" x2="200" y2="112" stroke="currentColor" stroke-opacity="0.18" />
      <line v-if="hotIdx !== null && tip" :x1="tsX[hotIdx]" y1="10" :x2="tsX[hotIdx]" y2="112" stroke="currentColor" stroke-opacity="0.25" stroke-dasharray="3 4" />
      <path
        v-for="(s, i) in tsSeries" :key="i"
        class="viz-line" :d="s.d" fill="none" :stroke="s.c" stroke-width="2" stroke-linecap="round"
        :style="{ animationDelay: s.delay + 's' }"
      />
      <circle class="viz-dot" cx="200" cy="26" r="3" :fill="VIOLET" style="animation-delay: 1.9s" />
      <circle class="viz-dot" cx="200" cy="46" r="3" :fill="CYAN" style="animation-delay: 2.1s" />
      <circle class="viz-dot" cx="200" cy="72" r="3" :fill="EMERALD" style="animation-delay: 2.3s" />
    </svg>

    <!-- HEATMAP -->
    <svg v-else-if="kind === 'heat'" viewBox="0 0 200 120" class="w-full h-full cursor-crosshair" aria-hidden="true" @pointermove="onHeat">
      <g>
        <rect
          v-for="(v, i) in heatData" :key="i"
          class="viz-dot vz-el" :class="{ 'vz-hot': hotIdx === i }"
          :x="4 + (i % heatCols) * 19.5" :y="8 + Math.floor(i / heatCols) * 18.5"
          width="16" height="15" rx="3"
          :fill="VIOLET" :fill-opacity="hotIdx === i ? 1 : 0.08 + (v / 9) * 0.85"
          :stroke="hotIdx === i ? 'white' : 'none'" stroke-opacity="0.5"
          :style="{ animationDelay: ((i % heatCols) * 0.05 + Math.floor(i / heatCols) * 0.07) + 's' }"
        />
      </g>
    </svg>

    <!-- shared tooltip -->
    <Transition name="vz-tip">
      <div
        v-if="tip"
        class="absolute z-10 pointer-events-none -translate-x-1/2 -translate-y-full rounded-lg border bg-popover/95 backdrop-blur px-2.5 py-1.5 shadow-lg shadow-black/40 whitespace-nowrap"
        :style="{ left: tip.x + 'px', top: tip.y + 'px' }"
      >
        <div class="text-[9px] font-semibold uppercase tracking-wider text-muted-foreground">{{ tip.head }}</div>
        <div v-for="(r, i) in tip.rows" :key="i" class="flex items-center gap-1.5 text-[11px]">
          <span class="h-1.5 w-1.5 rounded-full shrink-0" :style="{ background: r.c }" />
          <span class="tabular-nums font-medium">{{ r.t }}</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.vz-el { transition: opacity 200ms ease, transform 200ms ease; }
.vz-dim { opacity: 0.45; }
.vz-hot { filter: brightness(1.25); }
.vz-tip-enter-active, .vz-tip-leave-active { transition: opacity 140ms ease, transform 140ms ease; }
.vz-tip-enter-from, .vz-tip-leave-to { opacity: 0; transform: translate(-50%, calc(-100% + 4px)); }
</style>
