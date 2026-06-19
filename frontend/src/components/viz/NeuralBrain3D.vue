<!--
  NeuralBrain3D — a real 3D brain made of neurons + synapses, rendered to canvas
  (no WebGL lib). Neurons sit on a bumpy, two-hemisphere ellipsoid (cortex) plus
  some interior; nearest neighbours are wired with synapse edges; pulses fire
  along edges (a bright dot travelling node→node). The brain auto-rotates and
  parallax-tilts toward the cursor. TRON red neurons, red synaptic pulses.
-->
<template>
  <canvas ref="cv" class="brain" aria-hidden="true"></canvas>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'

const N = 720                 // neurons
const cv = ref<HTMLCanvasElement | null>(null)
let ctx!: CanvasRenderingContext2D
let host!: HTMLElement
let raf = 0
let ro: ResizeObserver | null = null
let w = 0, h = 0, dpr = 1, reduce = false

// neuron buffers (unit-ish brain space) + per-neuron flash energy
const nx = new Float32Array(N), ny = new Float32Array(N), nz = new Float32Array(N)
const flash = new Float32Array(N)
type Edge = { a: number; b: number }
let edges: Edge[] = []
type Pulse = { e: number; t: number; sp: number }
let pulses: Pulse[] = []

let spin = 0
let mx = 0, my = 0, smx = 0, smy = 0
let lastSpawn = 0

function buildBrain() {
  // --- neuron positions: bumpy two-hemisphere ellipsoid (cortex) + interior ---
  for (let i = 0; i < N; i++) {
    const u = Math.random() * Math.PI * 2
    const v = Math.acos(2 * Math.random() - 1)
    let x = Math.sin(v) * Math.cos(u)
    let y = Math.sin(v) * Math.sin(u)
    let z = Math.cos(v)
    const surface = Math.random() > 0.22
    const rad = surface ? 1 : 0.45 + Math.random() * 0.5       // shell vs interior
    // gyri/sulci bumps for a cortex look
    const bump = 1 + 0.13 * Math.sin(u * 6.0) * Math.sin(v * 5.0)
    x *= 1.0 * rad * bump        // x = brain width (widest)
    y *= 0.72 * rad * bump       // y = height
    z *= 0.86 * rad * bump       // z = front-back
    // split into L/R hemispheres with a longitudinal-fissure gap
    x += (x >= 0 ? 1 : -1) * 0.07
    y -= 0.05                    // sit slightly low like a real brain
    nx[i] = x; ny[i] = y; nz[i] = z
  }
  // --- synapses: connect each neuron to its ~2 nearest neighbours ---
  edges = []
  const seen = new Set<string>()
  for (let i = 0; i < N; i++) {
    const cand: { j: number; d: number }[] = []
    for (let j = 0; j < N; j++) {
      if (j === i) continue
      const dx = nx[i] - nx[j], dy = ny[i] - ny[j], dz = nz[i] - nz[j]
      cand.push({ j, d: dx * dx + dy * dy + dz * dz })
    }
    cand.sort((p, q) => p.d - q.d)
    const k = 2 + (Math.random() < 0.4 ? 1 : 0)
    for (let n = 0; n < k; n++) {
      const j = cand[n].j
      const key = i < j ? `${i}_${j}` : `${j}_${i}`
      if (seen.has(key)) continue
      seen.add(key)
      edges.push({ a: i, b: j })
    }
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

const FOCAL = 3.0
function frame(t: number) {
  if (!reduce) spin = t * 0.00018
  smx += (mx - smx) * 0.05
  smy += (my - smy) * 0.05
  const ay = spin + smx * 1.0
  const ax = 0.18 + smy * 0.35
  const cosY = Math.cos(ay), sinY = Math.sin(ay), cosX = Math.cos(ax), sinX = Math.sin(ax)
  const scale = Math.min(w, h) * 0.4
  const cx = w * 0.5, cy = h * 0.5

  // project all neurons to screen
  const sxArr = new Float32Array(N), syArr = new Float32Array(N), spArr = new Float32Array(N)
  for (let i = 0; i < N; i++) {
    const x1 = nx[i] * cosY + nz[i] * sinY
    const z1 = -nx[i] * sinY + nz[i] * cosY
    const y2 = ny[i] * cosX - z1 * sinX
    const z2 = ny[i] * sinX + z1 * cosX
    const p = FOCAL / (FOCAL + z2)
    sxArr[i] = cx + x1 * scale * p
    syArr[i] = cy + y2 * scale * p
    spArr[i] = p
    flash[i] *= 0.92            // decay neuron flash
  }

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, w, h)

  // soft core glow
  ctx.globalCompositeOperation = 'lighter'
  const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, scale * 0.95)
  g.addColorStop(0, 'rgba(255, 6, 10,0.16)')
  g.addColorStop(1, 'rgba(255, 6, 10,0)')
  ctx.fillStyle = g
  ctx.beginPath(); ctx.arc(cx, cy, scale * 0.95, 0, 6.2832); ctx.fill()

  // synapse edges (faint red wiring)
  ctx.globalCompositeOperation = 'source-over'
  ctx.lineWidth = 1
  for (const e of edges) {
    const pa = spArr[e.a], pb = spArr[e.b]
    const alpha = Math.max(0, Math.min(0.4, (pa + pb - 1.4) * 0.5)) * 0.5 + 0.04
    ctx.strokeStyle = `rgba(255, 92, 96, ${alpha})`
    ctx.beginPath(); ctx.moveTo(sxArr[e.a], syArr[e.a]); ctx.lineTo(sxArr[e.b], syArr[e.b]); ctx.stroke()
  }

  // spawn + advance pulses
  if (!reduce && t - lastSpawn > 90 && pulses.length < 70 && edges.length) {
    lastSpawn = t
    const e = (Math.random() * edges.length) | 0
    pulses.push({ e, t: 0, sp: 0.012 + Math.random() * 0.02 })
  }
  ctx.globalCompositeOperation = 'lighter'
  pulses = pulses.filter((pu) => {
    pu.t += reduce ? 0 : pu.sp
    if (pu.t >= 1) { flash[edges[pu.e].b] = 1; return false }
    const e = edges[pu.e]
    const x = sxArr[e.a] + (sxArr[e.b] - sxArr[e.a]) * pu.t
    const y = syArr[e.a] + (syArr[e.b] - syArr[e.a]) * pu.t
    ctx.fillStyle = 'rgba(255, 77, 81, 0.9)'
    ctx.beginPath(); ctx.arc(x, y, 1.7, 0, 6.2832); ctx.fill()
    return true
  })

  // neurons (on top) — TRON red, brighter when recently fired / nearer camera
  ctx.globalCompositeOperation = 'source-over'
  for (let i = 0; i < N; i++) {
    const p = spArr[i]
    const depth = Math.max(0, Math.min(1, (p - 0.7) / 0.7))
    const fl = flash[i]
    const a = Math.min(1, 0.28 + depth * 0.5 + fl * 0.5)
    const r = (0.8 + depth * 1.1) * (1 + fl * 1.6)
    // fired neurons flash toward warm-white, resting are TRON red
    const cr = 255 | 0, cg = (6 + fl * 120) | 0, cb = (10 + fl * 150) | 0
    ctx.fillStyle = `rgba(${cr},${cg},${cb},${a})`
    ctx.beginPath(); ctx.arc(sxArr[i], syArr[i], r, 0, 6.2832); ctx.fill()
  }

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
  buildBrain()
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
.brain { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
</style>
