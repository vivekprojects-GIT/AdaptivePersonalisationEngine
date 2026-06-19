<!--
  FormatField — a backdrop that states APE's core idea: it picks among many answer
  FORMATS. Tiny format glyphs (table, bar chart, bullets, decision card, numbered
  steps, one-liner) drift through depth on a slowly rotating 3D field and parallax
  toward the cursor. One glyph near the centre is "selected" (brighter gold, with a
  halo) — the chosen format. Subtle, canvas-drawn, no dependency.
-->
<template>
  <canvas ref="cv" class="ffield" aria-hidden="true"></canvas>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'

type Kind = 'table' | 'bars' | 'bullets' | 'card' | 'steps' | 'line'
const KINDS: Kind[] = ['table', 'bars', 'bullets', 'card', 'steps', 'line']
const COUNT = 44

type G = { x: number; y: number; z: number; vx: number; vy: number; vz: number; kind: Kind; rot: number; vr: number }
let glyphs: G[] = []

const cv = ref<HTMLCanvasElement | null>(null)
let ctx!: CanvasRenderingContext2D
let host!: HTMLElement
let raf = 0, ro: ResizeObserver | null = null
let w = 0, h = 0, dpr = 1, reduce = false
let mx = 0, my = 0, smx = 0, smy = 0
let spin = 0   // continuous 3D auto-rotation of the whole field

function rnd(a: number, b: number) { return a + Math.random() * (b - a) }

function build() {
  glyphs = []
  for (let i = 0; i < COUNT; i++) {
    glyphs.push({
      x: rnd(-1.15, 1.15), y: rnd(-1.1, 1.1), z: rnd(-1, 1),
      vx: rnd(-0.02, 0.02), vy: rnd(-0.012, 0.012), vz: rnd(-0.02, 0.02),
      kind: KINDS[i % KINDS.length],
      rot: rnd(-0.18, 0.18), vr: rnd(-0.06, 0.06),
    })
  }
}

function resize() {
  if (!cv.value || !host) return
  const r = host.getBoundingClientRect()
  w = Math.max(1, r.width); h = Math.max(1, r.height)
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  cv.value.width = w * dpr; cv.value.height = h * dpr
  cv.value.style.width = w + 'px'; cv.value.style.height = h + 'px'
}

// draw one format glyph centred at (0,0), unit size ~ s, in the given colour
function drawGlyph(kind: Kind, s: number, colour: string) {
  ctx.lineWidth = Math.max(0.8, s * 0.05)
  ctx.strokeStyle = colour; ctx.fillStyle = colour
  const hw = s * 0.62, hh = s * 0.46
  if (kind === 'table') {
    ctx.strokeRect(-hw, -hh, hw * 2, hh * 2)
    ctx.beginPath(); ctx.moveTo(-hw, -hh * 0.2); ctx.lineTo(hw, -hh * 0.2)
    ctx.moveTo(-hw, hh * 0.45); ctx.lineTo(hw, hh * 0.45)
    ctx.moveTo(0, -hh); ctx.lineTo(0, hh); ctx.stroke()
  } else if (kind === 'bars') {
    const bw = s * 0.18
    const hs = [0.5, 0.85, 0.35, 0.7]
    for (let i = 0; i < 4; i++) { const x = -hw + i * (bw + s * 0.08); const bh = hh * 2 * hs[i]; ctx.fillRect(x, hh - bh, bw, bh) }
  } else if (kind === 'bullets') {
    for (let i = 0; i < 3; i++) { const y = -hh + i * hh; ctx.beginPath(); ctx.arc(-hw + s * 0.08, y, s * 0.06, 0, 6.28); ctx.fill(); ctx.beginPath(); ctx.moveTo(-hw + s * 0.24, y); ctx.lineTo(hw, y); ctx.stroke() }
  } else if (kind === 'card') {
    const rr = s * 0.12; roundRect(-hw, -hh, hw * 2, hh * 2, rr); ctx.stroke()
    ctx.fillRect(-hw + s * 0.14, -hh + s * 0.16, s * 0.5, s * 0.1)
    ctx.globalAlpha *= 0.6; ctx.fillRect(-hw + s * 0.14, 0, s * 0.9, s * 0.07); ctx.fillRect(-hw + s * 0.14, s * 0.18, s * 0.65, s * 0.07); ctx.globalAlpha /= 0.6
  } else if (kind === 'steps') {
    for (let i = 0; i < 3; i++) { const y = -hh + i * hh; ctx.beginPath(); ctx.arc(-hw + s * 0.1, y, s * 0.12, 0, 6.28); ctx.stroke(); ctx.beginPath(); ctx.moveTo(-hw + s * 0.3, y); ctx.lineTo(hw, y); ctx.stroke() }
  } else { // line / one-liner
    ctx.beginPath(); ctx.moveTo(-hw, 0); ctx.lineTo(hw, 0); ctx.lineWidth = s * 0.1; ctx.stroke()
  }
}
function roundRect(x: number, y: number, ww: number, hh: number, r: number) {
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + ww, y, x + ww, y + hh, r); ctx.arcTo(x + ww, y + hh, x, y + hh, r)
  ctx.arcTo(x, y + hh, x, y, r); ctx.arcTo(x, y, x + ww, y, r); ctx.closePath()
}

const FOCAL = 2.4
function frame() {
  smx += (mx - smx) * 0.05; smy += (my - smy) * 0.05
  if (!reduce) spin += 0.0017               // slow continuous 3D turn
  const ay = spin + smx * 0.45, ax = smy * 0.3   // auto-rotation + cursor parallax
  const cosY = Math.cos(ay), sinY = Math.sin(ay), cosX = Math.cos(ax), sinX = Math.sin(ax)
  const scale = Math.min(w, h) * 0.5
  const cx = w * 0.5, cy = h * 0.5
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, w, h)

  for (const g of glyphs) {
    if (!reduce) {
      g.x += g.vx * 0.016; g.y += g.vy * 0.016; g.z += g.vz * 0.016; g.rot += g.vr * 0.016
      if (g.x > 1.2) g.x = -1.2; if (g.x < -1.2) g.x = 1.2
      if (g.y > 1.15) g.y = -1.15; if (g.y < -1.15) g.y = 1.15
      if (g.z > 1) g.z = -1; if (g.z < -1) g.z = 1
    }
    // rotate the field for parallax
    const x1 = g.x * cosY + g.z * sinY
    const z1 = -g.x * sinY + g.z * cosY
    const y2 = g.y * cosX - z1 * sinX
    const z2 = g.y * sinX + z1 * cosX
    const p = FOCAL / (FOCAL + z2)
    if (p <= 0) continue
    const X = cx + x1 * scale * p
    const Y = cy + y2 * scale * p
    const depth = Math.max(0, Math.min(1, (p - 0.6) / 0.85))
    // the glyph nearest the centre + camera is "selected" → brighter gold, with a halo
    const dCentre = Math.hypot(x1, y2)
    const selected = dCentre < 0.3 && z2 < -0.25
    const baseA = 0.1 + depth * 0.32
    const a = selected ? Math.min(0.92, baseA + 0.5) : baseA
    // bright "chosen" pick, lighter red for bars/one-liner, TRON red for the rest
    const col = selected ? '255,90,94' : (g.kind === 'bars' || g.kind === 'line' ? '255,130,132' : '255,40,44')
    const s = (13 + depth * 28) * p * (selected ? 1.25 : 1)

    ctx.save()
    ctx.translate(X, Y)
    if (selected) {
      // soft violet halo behind the chosen format — APE's pick
      const halo = ctx.createRadialGradient(0, 0, 0, 0, 0, s * 1.8)
      halo.addColorStop(0, 'rgba(255, 6, 10,0.30)')
      halo.addColorStop(1, 'rgba(255, 6, 10,0)')
      ctx.globalAlpha = Math.min(1, depth + 0.45)
      ctx.fillStyle = halo
      ctx.beginPath(); ctx.arc(0, 0, s * 1.8, 0, 6.28); ctx.fill()
    }
    ctx.rotate(g.rot)
    ctx.globalAlpha = a
    drawGlyph(g.kind, s, `rgba(${col},1)`)
    ctx.restore()
    ctx.globalAlpha = 1
  }
  raf = requestAnimationFrame(frame)
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
.ffield { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; }
</style>
