<script setup lang="ts">
/** InteractiveChart, a real, Plotly-grade interactive chart in pure SVG.
 *
 *  · crosshair that tracks the pointer and snaps to the nearest data point
 *  · live tooltip with the x-label and every visible series value
 *  · clickable legend, toggle series on/off with smooth transitions
 *  · animated draw-in on mount
 *
 *  No chart library: ~9KB of Vue + SVG, theme-aware, touch-friendly.
 *  The data tells the product's story: format win-rates as APE learns.
 */
import { computed, ref } from 'vue'

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const SERIES = [
  { name: 'Comparisons → tables', color: '#0d9488', data: [42, 48, 55, 53, 61, 66, 64, 71, 74, 78, 81, 84] },
  { name: 'Definitions → one-liners', color: '#22d3ee', data: [30, 34, 33, 41, 45, 52, 55, 57, 63, 66, 65, 70] },
  { name: 'Everything → long prose', color: '#64748b', data: [58, 54, 50, 47, 44, 40, 42, 38, 35, 33, 30, 28] },
]

// chart geometry (viewBox units)
const W = 640
const H = 300
const M = { t: 18, r: 16, b: 34, l: 40 }
const IW = W - M.l - M.r
const IH = H - M.t - M.b
const Y_MAX = 100

const visible = ref(SERIES.map(() => true))
function toggle(i: number) {
  // never allow zero visible series
  const on = visible.value.filter(Boolean).length
  if (visible.value[i] && on === 1) return
  visible.value[i] = !visible.value[i]
}

function x(i: number) {
  return M.l + (i / (MONTHS.length - 1)) * IW
}
function y(v: number) {
  return M.t + IH - (v / Y_MAX) * IH
}

/** Catmull-Rom → cubic Bézier for a smooth, natural line. */
function smoothPath(data: number[]) {
  const pts = data.map((v, i) => [x(i), y(v)] as const)
  if (pts.length < 3) return `M${pts.map((p) => p.join(',')).join(' L')}`
  let d = `M${pts[0][0]},${pts[0][1]}`
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)]
    const p1 = pts[i]
    const p2 = pts[i + 1]
    const p3 = pts[Math.min(pts.length - 1, i + 2)]
    const c1x = p1[0] + (p2[0] - p0[0]) / 6
    const c1y = p1[1] + (p2[1] - p0[1]) / 6
    const c2x = p2[0] - (p3[0] - p1[0]) / 6
    const c2y = p2[1] - (p3[1] - p1[1]) / 6
    d += ` C${c1x.toFixed(1)},${c1y.toFixed(1)} ${c2x.toFixed(1)},${c2y.toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`
  }
  return d
}

const paths = computed(() => SERIES.map((s) => smoothPath(s.data)))
const gridY = [25, 50, 75, 100]

/* ---- pointer → crosshair + tooltip ---- */
const svgEl = ref<SVGSVGElement | null>(null)
const hoverIdx = ref<number | null>(null)
const tipPos = ref({ x: 0, y: 0 })

function onMove(e: PointerEvent) {
  const el = svgEl.value
  if (!el) return
  const r = el.getBoundingClientRect()
  const vx = ((e.clientX - r.left) / r.width) * W
  const i = Math.round(((vx - M.l) / IW) * (MONTHS.length - 1))
  hoverIdx.value = Math.max(0, Math.min(MONTHS.length - 1, i))
  // tooltip in CONTAINER pixels, clamped so it never clips
  const cx = (x(hoverIdx.value) / W) * r.width
  tipPos.value = { x: Math.min(Math.max(cx, 90), r.width - 90), y: 10 }
}
function onLeave() {
  hoverIdx.value = null
}
</script>

<template>
  <div class="relative select-none">
    <!-- legend -->
    <div class="flex flex-wrap items-center gap-2 mb-3">
      <button
        v-for="(s, i) in SERIES"
        :key="s.name"
        type="button"
        class="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-all"
        :class="visible[i] ? 'text-foreground/90 bg-background/50' : 'text-muted-foreground/50 opacity-60'"
        :aria-pressed="visible[i]"
        @click="toggle(i)"
      >
        <span class="h-2 w-2 rounded-full transition-opacity" :style="{ background: s.color, opacity: visible[i] ? 1 : 0.35 }" />
        {{ s.name }}
      </button>
      <span class="ml-auto text-[10px] text-muted-foreground hidden sm:inline">hover to inspect · click legend to toggle</span>
    </div>

    <svg
      ref="svgEl"
      :viewBox="`0 0 ${W} ${H}`"
      class="w-full h-auto cursor-crosshair"
      role="img"
      aria-label="Format win rate by month as APE learns: tables and one-liners rise while undifferentiated prose falls"
      @pointermove="onMove"
      @pointerleave="onLeave"
    >
      <!-- grid + axes -->
      <g>
        <line v-for="g in gridY" :key="g" :x1="M.l" :y1="y(g)" :x2="W - M.r" :y2="y(g)" stroke="currentColor" stroke-opacity="0.08" />
        <text v-for="g in gridY" :key="'t' + g" :x="M.l - 8" :y="y(g) + 3.5" text-anchor="end" class="ic-axis">{{ g }}%</text>
        <line :x1="M.l" :y1="y(0)" :x2="W - M.r" :y2="y(0)" stroke="currentColor" stroke-opacity="0.18" />
        <text v-for="(m, i) in MONTHS" :key="m" :x="x(i)" :y="H - 12" text-anchor="middle" class="ic-axis" :opacity="i % 2 ? 0.45 : 0.8">{{ m }}</text>
      </g>

      <!-- series -->
      <g v-for="(s, i) in SERIES" :key="s.name" class="ic-series" :style="{ opacity: visible[i] ? 1 : 0.06 }">
        <path :d="paths[i]" fill="none" :stroke="s.color" stroke-width="2.4" stroke-linecap="round" class="viz-line" :style="{ animationDelay: i * 0.3 + 's' }" />
      </g>

      <!-- crosshair + snapped markers -->
      <g v-if="hoverIdx !== null">
        <line :x1="x(hoverIdx)" :y1="M.t" :x2="x(hoverIdx)" :y2="H - M.b" stroke="currentColor" stroke-opacity="0.25" stroke-dasharray="3 4" />
        <template v-for="(s, i) in SERIES" :key="'m' + i">
          <g v-if="visible[i]">
            <circle :cx="x(hoverIdx)" :cy="y(s.data[hoverIdx])" r="7" :fill="s.color" opacity="0.18" />
            <circle :cx="x(hoverIdx)" :cy="y(s.data[hoverIdx])" r="3.4" :fill="s.color" stroke="var(--card)" stroke-width="1.5" />
          </g>
        </template>
      </g>
    </svg>

    <!-- tooltip -->
    <Transition name="ic-tip">
      <div
        v-if="hoverIdx !== null"
        class="absolute z-10 pointer-events-none -translate-x-1/2 rounded-xl border bg-popover/95 backdrop-blur px-3 py-2 shadow-lg shadow-black/40"
        :style="{ left: tipPos.x + 'px', top: tipPos.y + 'px' }"
      >
        <div class="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">{{ MONTHS[hoverIdx] }} · win rate</div>
        <div class="space-y-0.5">
          <template v-for="(s, i) in SERIES" :key="'tt' + i">
            <div v-if="visible[i]" class="flex items-center gap-2 text-[11.5px]">
              <span class="h-1.5 w-1.5 rounded-full shrink-0" :style="{ background: s.color }" />
              <span class="text-muted-foreground">{{ s.name.split(' → ')[1] }}</span>
              <span class="ml-auto pl-3 tabular-nums font-semibold">{{ s.data[hoverIdx] }}%</span>
            </div>
          </template>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.ic-axis {
  font-size: 10px;
  fill: var(--muted-foreground);
}
.ic-series {
  transition: opacity 360ms cubic-bezier(0.22, 1, 0.36, 1);
}
.ic-tip-enter-active,
.ic-tip-leave-active {
  transition: opacity 160ms ease, transform 160ms ease;
}
.ic-tip-enter-from,
.ic-tip-leave-to {
  opacity: 0;
  transform: translate(-50%, 4px);
}
</style>
