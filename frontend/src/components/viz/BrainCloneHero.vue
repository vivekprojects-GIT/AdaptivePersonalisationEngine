<!--
  BrainCloneHero — the Personalisation visual. A reader's mind (left, cool white)
  and APE's learned preference map of that reader (right, TRON red). Six DECIDE
  intents (Decision · Explanation · Comparison · Instructional · Definitional ·
  Evaluation) stream across the bridge between them; as each fires, APE's side
  lights up — APE learning which answer format the reader prefers, per intent.

  Dependency-free: a shared neuron cloud is projected twice (the right side is the
  left reflected across the centre, so it is literally a clone), rotated in 3D with
  cursor parallax. Respects prefers-reduced-motion.
-->
<template>
  <canvas ref="cv" class="bclone" aria-hidden="true"></canvas>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'

// The six DECIDE intents — the lanes that flow from the human mind to its clone.
const INTENTS = ['Decision', 'Explanation', 'Comparison', 'Instructional', 'Definitional', 'Evaluation']

type N = { lx: number; ly: number; lz: number; ph: number }
let neurons: N[] = []
let edges: [number, number][] = []
const PER = 168

type P = { lane: number; t: number; sp: number }
let parts: P[] = []

const cv = ref<HTMLCanvasElement | null>(null)
let ctx!: CanvasRenderingContext2D
let host!: HTMLElement
let raf = 0, ro: ResizeObserver | null = null
let w = 0, h = 0, dpr = 1, reduce = false
let mx = 0, my = 0, smx = 0, smy = 0
let tt = 0

const FOCAL = 2.6
const SEP = 0.66          // half the distance between the two brain centres
const rnd = (a: number, b: number) => a + Math.random() * (b - a)
const laneY = (k: number) => -0.30 + k * (0.60 / (INTENTS.length - 1))

function build() {
  neurons = []
  for (let i = 0; i < PER; i++) {
    const u = Math.random() * Math.PI * 2
    const v = Math.acos(rnd(-1, 1))
    const bump = 1 + 0.13 * Math.sin(u * 5) * Math.sin(v * 4)
    let lx = Math.cos(u) * Math.sin(v) * 0.42 * bump
    const ly = Math.cos(v) * 0.34 * bump
    const lz = Math.sin(u) * Math.sin(v) * 0.40 * bump
    // carve a midline fissure → two hemispheres
    const side = lx >= 0 ? 1 : -1
    lx = side * (Math.abs(lx) * 0.88 + 0.05)
    neurons.push({ lx, ly, lz, ph: Math.random() * Math.PI * 2 })
  }
  // nearest-two-neighbour synapse edges (shared topology for both brains)
  edges = []
  for (let i = 0; i < PER; i++) {
    let b1 = -1, d1 = 1e9, b2 = -1, d2 = 1e9
    for (let j = 0; j < PER; j++) {
      if (i === j) continue
      const dx = neurons[i].lx - neurons[j].lx, dy = neurons[i].ly - neurons[j].ly, dz = neurons[i].lz - neurons[j].lz
      const d = dx * dx + dy * dy + dz * dz
      if (d < d1) { d2 = d1; b2 = b1; d1 = d; b1 = j } else if (d < d2) { d2 = d; b2 = j }
    }
    if (b1 > i) edges.push([i, b1])
    if (b2 > i) edges.push([i, b2])
  }
  parts = []
  for (let i = 0; i < 40; i++) parts.push({ lane: i % INTENTS.length, t: Math.random(), sp: rnd(0.4, 0.8) })
}

function resize() {
  if (!cv.value || !host) return
  const r = host.getBoundingClientRect()
  w = Math.max(1, r.width); h = Math.max(1, r.height)
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  cv.value.width = w * dpr; cv.value.height = h * dpr
  cv.value.style.width = w + 'px'; cv.value.style.height = h + 'px'
}

let cx = 0, cy = 0, scale = 1, cosAy = 1, sinAy = 0, cosAx = 1, sinAx = 0
function proj(wx: number, wy: number, wz: number) {
  const x1 = wx * cosAy + wz * sinAy
  const z1 = -wx * sinAy + wz * cosAy
  const y2 = wy * cosAx - z1 * sinAx
  const z2 = wy * sinAx + z1 * cosAx
  const p = FOCAL / (FOCAL + z2)
  return { X: cx + x1 * scale * p, Y: cy + y2 * scale * p, z: z2, p }
}

function frame() {
  raf = requestAnimationFrame(frame)
  if (typeof document !== 'undefined' && document.hidden) return
  if (!reduce) tt += 0.016
  smx += (mx - smx) * 0.05; smy += (my - smy) * 0.05
  const wob = reduce ? 0 : Math.sin(tt * 0.25) * 0.28          // slow 3D turn
  const ay = wob + smx * 0.5, ax = -0.06 + smy * 0.32
  cosAy = Math.cos(ay); sinAy = Math.sin(ay); cosAx = Math.cos(ax); sinAx = Math.sin(ax)
  scale = Math.min(w, h) * 0.66
  cx = w * 0.5; cy = h * 0.52

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, w, h)

  const active = Math.floor(tt / 1.5) % INTENTS.length

  // ambient glows behind each brain
  const gh = proj(-SEP, 0, 0), ga = proj(SEP, 0, 0)
  paintGlow(gh.X, gh.Y, scale * 0.62, '210,210,224', 0.05)
  paintGlow(ga.X, ga.Y, scale * 0.66, '255,6,10', 0.13)

  // both brains, far depth first
  drawBrain(-1)   // human (left)
  drawBrain(1)    // ai clone (right)

  // DECIDE bridge — beams, particles, labels
  drawBridge(active)

  // side labels
  label(gh.X, gh.Y + scale * 0.5, 'THE READER', '220,220,230', 0.34, 11)
  label(ga.X, ga.Y + scale * 0.52, 'APE’S PREFERENCE MAP', '255,80,84', 0.55, 11)
}

function paintGlow(X: number, Y: number, r: number, rgb: string, a: number) {
  const g = ctx.createRadialGradient(X, Y, 0, X, Y, r)
  g.addColorStop(0, `rgba(${rgb},${a})`); g.addColorStop(1, `rgba(${rgb},0)`)
  ctx.fillStyle = g
  ctx.beginPath(); ctx.arc(X, Y, r, 0, 6.2832); ctx.fill()
}

function drawBrain(sideSign: number) {
  const ai = sideSign > 0
  // mirror-clone: right brain = left brain reflected across x=0
  const wx = (n: N) => ai ? (-n.lx + SEP) : (n.lx - SEP)
  const phase = ai ? 1.1 : 0   // the clone fires just after the human (learning lag)

  // synapses
  ctx.lineWidth = 1
  for (const [a, b] of edges) {
    const na = neurons[a], nb = neurons[b]
    const pa = proj(wx(na), na.ly, na.lz), pb = proj(wx(nb), nb.ly, nb.lz)
    const dep = Math.max(0, Math.min(1, (pa.p - 0.62) / 0.7))
    const al = (ai ? 0.10 : 0.07) + dep * 0.10
    ctx.strokeStyle = ai ? `rgba(255, 56, 60,${al})` : `rgba(150,150,164,${al})`
    ctx.beginPath(); ctx.moveTo(pa.X, pa.Y); ctx.lineTo(pb.X, pb.Y); ctx.stroke()
  }
  // neurons (additive for glow)
  ctx.globalCompositeOperation = 'lighter'
  for (const n of neurons) {
    const pr = proj(wx(n), n.ly, n.lz)
    if (pr.p <= 0) continue
    const dep = Math.max(0, Math.min(1, (pr.p - 0.58) / 0.8))
    const fl = 0.5 + 0.5 * Math.sin(tt * 2.2 + n.ph + phase)   // firing pulse
    const flash = Math.pow(Math.max(0, fl), 3)
    const rad = (0.7 + dep * 1.7) * pr.p + flash * 1.4
    let rgb: string
    if (ai) rgb = `255,${6 + flash * 110 | 0},${10 + flash * 130 | 0}`                       // TRON red → warm white
    else rgb = `${205 + flash * 50 | 0},${207 + flash * 48 | 0},${220 + flash * 35 | 0}`      // cool white
    const al = (0.18 + dep * 0.5) + flash * 0.4
    ctx.fillStyle = `rgba(${rgb},${Math.min(1, al)})`
    ctx.beginPath(); ctx.arc(pr.X, pr.Y, rad, 0, 6.2832); ctx.fill()
  }
  ctx.globalCompositeOperation = 'source-over'
}

function drawBridge(active: number) {
  // beams + particles per DECIDE lane
  for (let k = 0; k < INTENTS.length; k++) {
    const y = laneY(k)
    const isOn = k === active
    const arc = 0.12 + 0.05 * Math.sin(k * 1.7)   // bulge toward viewer
    const A = proj(-0.30, y, arc), B = proj(0.30, y, arc)
    // faint beam line spanning the gap between the two minds
    ctx.strokeStyle = isOn ? 'rgba(255, 77, 81,0.30)' : 'rgba(255, 6, 10,0.07)'
    ctx.lineWidth = isOn ? 1.4 : 0.8
    ctx.beginPath(); ctx.moveTo(A.X, A.Y); ctx.lineTo(B.X, B.Y); ctx.stroke()
    // label cascades left→right across the bridge so the six intents stay legible
    const M = proj(-0.14 + k * 0.055, y, arc + 0.02)
    label(M.X, M.Y - 9, INTENTS[k], isOn ? '255,80,84' : '210,210,224', isOn ? 0.9 : 0.3, isOn ? 12 : 10.5)
  }
  // particles flowing human → clone
  ctx.globalCompositeOperation = 'lighter'
  for (const p of parts) {
    if (!reduce) { p.t += p.sp * 0.016; if (p.t > 1) { p.t = 0; p.lane = Math.floor(Math.random() * INTENTS.length) } }
    const y = laneY(p.lane)
    const arc = 0.12 + 0.05 * Math.sin(p.lane * 1.7)
    const x = -0.30 + p.t * 0.60
    const z = arc + Math.sin(p.t * Math.PI) * 0.06
    const pr = proj(x, y, z)
    const on = p.lane === active
    const a = (on ? 0.9 : 0.4) * Math.sin(p.t * Math.PI)
    ctx.fillStyle = `rgba(255,${60 - p.t * 30 | 0},${64 + p.t * 40 | 0},${Math.max(0, a)})`
    ctx.beginPath(); ctx.arc(pr.X, pr.Y, (1.4 + (on ? 1.2 : 0)) * pr.p, 0, 6.2832); ctx.fill()
  }
  ctx.globalCompositeOperation = 'source-over'
}

function label(X: number, Y: number, text: string, rgb: string, a: number, size: number) {
  ctx.font = `600 ${size}px 'JetBrains Mono', ui-monospace, monospace`
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
  ctx.fillStyle = `rgba(${rgb},${a})`
  ctx.fillText(text, X, Y)
}

function onMove(e: PointerEvent) { const r = host.getBoundingClientRect(); mx = (e.clientX - r.left) / r.width - 0.5; my = (e.clientY - r.top) / r.height - 0.5 }
function onLeave() { mx = 0; my = 0 }

onMounted(() => {
  const el = cv.value; if (!el) return
  ctx = el.getContext('2d') as CanvasRenderingContext2D
  host = el.parentElement as HTMLElement
  reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  build(); resize()
  ro = new ResizeObserver(() => resize()); ro.observe(host)
  host.addEventListener('pointermove', onMove, { passive: true })
  host.addEventListener('pointerleave', onLeave, { passive: true })
  raf = requestAnimationFrame(frame)
})
onBeforeUnmount(() => {
  cancelAnimationFrame(raf); ro && ro.disconnect()
  if (host) { host.removeEventListener('pointermove', onMove); host.removeEventListener('pointerleave', onLeave) }
})
</script>

<style scoped>
.bclone { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; }
</style>
