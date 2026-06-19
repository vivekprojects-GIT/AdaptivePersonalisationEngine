<!--
  Galaxy3D — a real 3D spiral galaxy rendered to canvas (no WebGL lib). Stars are
  positioned in 3D (spiral arms + disc thickness), rotated around Y (slow spin),
  tilted on X (seen at an angle), and projected with perspective so near stars are
  bigger/brighter than far ones. The pointer parallax-tilts the whole galaxy.
  Cosmic palette: warm-white core → TRON red → deep red rim, with an additive core glow.
-->
<template>
  <canvas ref="cv" class="galaxy" aria-hidden="true"></canvas>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'

const COUNT = 2800
const BRANCHES = 3
const SPIN = 1.2            // how tightly the arms curl
const SCATTER = 0.36       // random spread around the arms
const TILT = 1.12          // base view tilt (rotateX) — disc seen at ~64°
const FOCAL = 2.3          // perspective strength

const cv = ref<HTMLCanvasElement | null>(null)
let ctx!: CanvasRenderingContext2D
let host!: HTMLElement
let raf = 0
let ro: ResizeObserver | null = null
let w = 0, h = 0, dpr = 1, reduce = false

// star buffers (positions in normalized radius 0..1, plus per-star color/seed)
const px = new Float32Array(COUNT), py = new Float32Array(COUNT), pz = new Float32Array(COUNT)
const cr = new Uint8Array(COUNT), cg = new Uint8Array(COUNT), cb = new Uint8Array(COUNT)
const rnd = new Float32Array(COUNT)

let mx = 0, my = 0, smx = 0, smy = 0   // pointer (normalized -0.5..0.5) + smoothed
let spin = 0

const lerp = (a: number, b: number, t: number) => a + (b - a) * t

function buildStars() {
  const CORE = [255, 245, 232], MID = [255, 90, 94], EDGE = [255, 6, 10]
  for (let i = 0; i < COUNT; i++) {
    const r = Math.pow(Math.random(), 1.6)              // denser toward the core
    const branch = (i % BRANCHES) / BRANCHES * Math.PI * 2
    const curl = r * SPIN
    const sx = (Math.random() - 0.5) * SCATTER * (0.35 + r)
    const sy = (Math.random() - 0.5) * SCATTER * 0.5 * Math.exp(-r * 2.4) // thin disc
    const sz = (Math.random() - 0.5) * SCATTER * (0.35 + r)
    px[i] = Math.cos(branch + curl) * r + sx
    py[i] = sy
    pz[i] = Math.sin(branch + curl) * r + sz
    rnd[i] = Math.random()
    const t = Math.min(1, r)
    let R: number, G: number, B: number
    if (t < 0.5) { const u = t / 0.5; R = lerp(CORE[0], MID[0], u); G = lerp(CORE[1], MID[1], u); B = lerp(CORE[2], MID[2], u) }
    else { const u = (t - 0.5) / 0.5; R = lerp(MID[0], EDGE[0], u); G = lerp(MID[1], EDGE[1], u); B = lerp(MID[2], EDGE[2], u) }
    cr[i] = R | 0; cg[i] = G | 0; cb[i] = B | 0
  }
}

function resize() {
  if (!cv.value || !host) return
  const rect = host.getBoundingClientRect()
  w = Math.max(1, rect.width); h = Math.max(1, rect.height)
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  cv.value.width = w * dpr; cv.value.height = h * dpr
  cv.value.style.width = w + 'px'; cv.value.style.height = h + 'px'
}

function frame(t: number) {
  if (!reduce) spin = t * 0.00006
  smx += (mx - smx) * 0.045
  smy += (my - smy) * 0.045
  const ay = spin + smx * 0.9                 // rotateY: auto-spin + pointer
  const ax = TILT + smy * 0.3                 // rotateX: tilt + pointer
  const cosY = Math.cos(ay), sinY = Math.sin(ay), cosX = Math.cos(ax), sinX = Math.sin(ax)
  const scale = Math.min(w, h) * 0.5
  const cx = w * 0.5, cy = h * 0.47

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, w, h)
  ctx.globalCompositeOperation = 'lighter'   // additive → stars glow where they overlap

  // galactic core glow (origin always projects to centre)
  const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, scale * 0.55)
  g.addColorStop(0, 'rgba(255, 77, 81, 0.45)')
  g.addColorStop(0.35, 'rgba(255, 6, 10,0.16)')
  g.addColorStop(1, 'rgba(255, 6, 10,0)')
  ctx.fillStyle = g
  ctx.beginPath(); ctx.arc(cx, cy, scale * 0.55, 0, 6.2832); ctx.fill()

  for (let i = 0; i < COUNT; i++) {
    const ox = px[i], oy = py[i], oz = pz[i]
    const x1 = ox * cosY + oz * sinY          // rotate Y
    const z1 = -ox * sinY + oz * cosY
    const y2 = oy * cosX - z1 * sinX           // rotate X (tilt)
    const z2 = oy * sinX + z1 * cosX
    const persp = FOCAL / (FOCAL + z2)         // perspective
    if (persp <= 0) continue
    const X = cx + x1 * scale * persp
    const Y = cy + y2 * scale * persp
    const tw = reduce ? 1 : (0.6 + 0.4 * Math.sin(t * 0.002 + rnd[i] * 6.283))
    const depth = persp > 1 ? 1 : Math.max(0, (persp - 0.6) / 0.9)
    const alpha = Math.min(1, (0.16 + depth * 0.72) * tw)
    const size = Math.max(0.4, (0.55 + rnd[i] * 0.9) * persp * 1.35)
    ctx.fillStyle = `rgba(${cr[i]},${cg[i]},${cb[i]},${alpha})`
    ctx.beginPath(); ctx.arc(X, Y, size, 0, 6.2832); ctx.fill()
  }

  ctx.globalCompositeOperation = 'source-over'
  raf = requestAnimationFrame(frame)
}

function onMove(e: PointerEvent) {
  const rect = host.getBoundingClientRect()
  mx = (e.clientX - rect.left) / rect.width - 0.5
  my = (e.clientY - rect.top) / rect.height - 0.5
}
function onLeave() { mx = 0; my = 0 }

onMounted(() => {
  const el = cv.value
  if (!el) return
  ctx = el.getContext('2d') as CanvasRenderingContext2D
  host = el.parentElement as HTMLElement
  reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  buildStars()
  resize()
  ro = new ResizeObserver(() => resize()); ro.observe(host)
  host.addEventListener('pointermove', onMove, { passive: true })
  host.addEventListener('pointerleave', onLeave, { passive: true })
  raf = requestAnimationFrame(frame)
})
onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  ro && ro.disconnect()
  if (host) { host.removeEventListener('pointermove', onMove); host.removeEventListener('pointerleave', onLeave) }
})
</script>

<style scoped>
.galaxy {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}
</style>
