<!--
  Interactive dot grid — Ramp-style dotted backdrop with a 3D cursor bulge.
  Dots within `influence` px of the (smoothed) pointer grow, darken, and push
  outward, so the grid reads as a soft depth lens that tracks the cursor.
  Canvas-based + rAF; pointer-events:none so it never blocks the content.
-->
<template>
  <canvas ref="cv" class="dot-grid" aria-hidden="true"></canvas>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'

const props = withDefaults(defineProps<{
  gap?: number        // px spacing between dots
  dotRadius?: number  // base dot radius
  influence?: number  // cursor influence radius (px)
  grow?: number       // max extra scale at the cursor
}>(), { gap: 26, dotRadius: 1.5, influence: 150, grow: 2.6 })

// far = resting dot color (cool gray-blue); near = lifted/darkened blue ink.
// Starfield: dim blue-white stars at rest, brightening to violet-white near the
// cursor (a "constellation lens" gliding through the field).
const FAR = [168, 178, 224]
const NEAR = [206, 188, 255]

const cv = ref<HTMLCanvasElement | null>(null)
let ctx!: CanvasRenderingContext2D
let host!: HTMLElement
let raf = 0
let ro: ResizeObserver | null = null
let dots: { x: number; y: number; ph: number; sz: number }[] = []
let w = 0, h = 0, dpr = 1
let mx = -1e4, my = -1e4     // target pointer (host-relative)
let cx = -1e4, cy = -1e4     // smoothed cursor
let reduce = false, seen = false

function build() {
  const el = cv.value
  if (!el || !host) return
  const rect = host.getBoundingClientRect()
  w = Math.max(1, rect.width); h = Math.max(1, rect.height)
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  el.width = w * dpr; el.height = h * dpr
  el.style.width = w + 'px'; el.style.height = h + 'px'
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  dots = []
  const cols = Math.ceil(w / props.gap) + 1
  const rows = Math.ceil(h / props.gap) + 1
  const ox = (w - (cols - 1) * props.gap) / 2
  const oy = (h - (rows - 1) * props.gap) / 2
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++) {
      const seed = Math.sin(r * 12.9898 + c * 78.233) * 43758.5453
      const frac = seed - Math.floor(seed)               // deterministic 0..1
      dots.push({
        x: ox + c * props.gap, y: oy + r * props.gap,
        ph: frac * 6.283,                                 // twinkle phase
        sz: 0.7 + frac * 0.7,                             // star-size variation
      })
    }
}

function frame() {
  // critically-damped cursor follow → the lens glides, not snaps.
  // reduced-motion: snap instantly + no displacement (still cursor-reactive).
  const k = reduce ? 1 : 0.14
  cx += (mx - cx) * k
  cy += (my - cy) * k
  const now = reduce ? 0 : performance.now()
  ctx.clearRect(0, 0, w, h)
  const R = props.influence
  for (const d of dots) {
    const dx = d.x - cx, dy = d.y - cy
    const dist = Math.hypot(dx, dy)
    let e = 0
    if (dist < R) { const t = 1 - dist / R; e = t * t } // eased 0..1 falloff
    const scale = 1 + e * props.grow                    // bigger = closer
    const twinkle = 0.26 + 0.16 * Math.sin(now * 0.0015 + d.ph) // stars breathe
    const alpha = twinkle + e * (0.95 - twinkle)        // brighten near cursor
    const push = reduce ? 0 : e * 7                     // 3D outward bulge
    const nx = dist > 0 ? dx / dist : 0
    const ny = dist > 0 ? dy / dist : 0
    const r = (FAR[0] + (NEAR[0] - FAR[0]) * e) | 0
    const g = (FAR[1] + (NEAR[1] - FAR[1]) * e) | 0
    const b = (FAR[2] + (NEAR[2] - FAR[2]) * e) | 0
    ctx.beginPath()
    ctx.arc(d.x + nx * push, d.y + ny * push, props.dotRadius * d.sz * scale, 0, 6.2832)
    ctx.fillStyle = `rgba(${r},${g},${b},${alpha})`
    ctx.fill()
  }
  raf = requestAnimationFrame(frame)
}

function onMove(e: PointerEvent) {
  const rect = host.getBoundingClientRect()
  mx = e.clientX - rect.left
  my = e.clientY - rect.top
  if (!seen) { seen = true; cx = mx; cy = my } // snap on first entry, no glide-in
}
function onLeave() { mx = -1e4; my = -1e4 }

onMounted(() => {
  const el = cv.value
  if (!el) return
  ctx = el.getContext('2d') as CanvasRenderingContext2D
  host = el.parentElement as HTMLElement
  reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  build()
  ro = new ResizeObserver(() => build()); ro.observe(host)
  host.addEventListener('pointermove', onMove, { passive: true })
  host.addEventListener('pointerleave', onLeave, { passive: true })
  // Always run the loop: nothing animates on its own (it only reacts to the
  // cursor), so this respects reduced-motion while keeping the canvas painted
  // through ResizeObserver-driven clears.
  raf = requestAnimationFrame(frame)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  ro && ro.disconnect()
  if (host) {
    host.removeEventListener('pointermove', onMove)
    host.removeEventListener('pointerleave', onLeave)
  }
})
</script>

<style scoped>
.dot-grid {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* clicks pass straight through to hero content */
  z-index: 0;
}
</style>
