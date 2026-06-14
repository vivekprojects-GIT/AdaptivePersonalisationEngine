<script setup lang="ts">
/** ParticleField — an interactive constellation rendered on <canvas>.
 *
 *  Drifting particles connect by proximity; the cursor gently repels them,
 *  so the field parts and reforms around the user's hand — the page feels
 *  alive and aware. Theme violet, DPR-aware, pauses when the tab is hidden,
 *  fully disabled under prefers-reduced-motion.
 */
import { onMounted, onUnmounted, ref } from 'vue'

const props = withDefaults(defineProps<{ count?: number; linkDist?: number }>(), {
  count: 70,
  linkDist: 120,
})

const canvas = ref<HTMLCanvasElement | null>(null)
let raf = 0
let running = false
let cleanup: (() => void) | null = null

type P = { x: number; y: number; vx: number; vy: number; r: number }

onMounted(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  const cv = canvas.value!
  const ctx = cv.getContext('2d')!
  const parent = cv.parentElement!

  let W = 0, H = 0, DPR = 1
  const mouse = { x: -9999, y: -9999 }
  const parts: P[] = []

  function size() {
    DPR = Math.min(2, window.devicePixelRatio || 1)
    W = parent.clientWidth
    H = parent.clientHeight
    cv.width = W * DPR
    cv.height = H * DPR
    cv.style.width = W + 'px'
    cv.style.height = H + 'px'
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0)
  }

  function seed() {
    parts.length = 0
    for (let i = 0; i < props.count; i++) {
      parts.push({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        r: 1 + Math.random() * 1.6,
      })
    }
  }

  function tick() {
    if (!running) return
    ctx.clearRect(0, 0, W, H)

    for (const p of parts) {
      // cursor repulsion — the field parts around the hand
      const dx = p.x - mouse.x
      const dy = p.y - mouse.y
      const d2 = dx * dx + dy * dy
      if (d2 < 16900) { // 130px
        const d = Math.sqrt(d2) || 1
        const f = (130 - d) / 130
        p.vx += (dx / d) * f * 0.5
        p.vy += (dy / d) * f * 0.5
      }
      // gentle damping keeps speeds sane after repulsion
      p.vx *= 0.985
      p.vy *= 0.985
      // baseline drift floor
      if (Math.abs(p.vx) < 0.05) p.vx += (Math.random() - 0.5) * 0.02
      if (Math.abs(p.vy) < 0.05) p.vy += (Math.random() - 0.5) * 0.02

      p.x += p.vx
      p.y += p.vy
      if (p.x < -10) p.x = W + 10
      if (p.x > W + 10) p.x = -10
      if (p.y < -10) p.y = H + 10
      if (p.y > H + 10) p.y = -10
    }

    // links
    for (let i = 0; i < parts.length; i++) {
      for (let j = i + 1; j < parts.length; j++) {
        const a = parts[i], b = parts[j]
        const dx = a.x - b.x, dy = a.y - b.y
        const d2 = dx * dx + dy * dy
        const max = props.linkDist
        if (d2 < max * max) {
          const alpha = (1 - Math.sqrt(d2) / max) * 0.22
          ctx.strokeStyle = `rgba(132, 204, 22, ${alpha.toFixed(3)})`
          ctx.lineWidth = 1
          ctx.beginPath()
          ctx.moveTo(a.x, a.y)
          ctx.lineTo(b.x, b.y)
          ctx.stroke()
        }
      }
    }

    // dots
    for (const p of parts) {
      ctx.fillStyle = 'rgba(132, 204, 22, 0.55)'
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fill()
    }

    raf = requestAnimationFrame(tick)
  }

  function onMove(e: PointerEvent) {
    const r = cv.getBoundingClientRect()
    mouse.x = e.clientX - r.left
    mouse.y = e.clientY - r.top
  }
  function onLeave() {
    mouse.x = -9999
    mouse.y = -9999
  }
  function onVis() {
    const want = !document.hidden
    if (want && !running) { running = true; raf = requestAnimationFrame(tick) }
    if (!want) { running = false; cancelAnimationFrame(raf) }
  }

  size()
  seed()
  running = true
  raf = requestAnimationFrame(tick)

  const ro = new ResizeObserver(() => { size() })
  ro.observe(parent)
  parent.addEventListener('pointermove', onMove, { passive: true })
  parent.addEventListener('pointerleave', onLeave, { passive: true })
  document.addEventListener('visibilitychange', onVis)

  cleanup = () => {
    running = false
    cancelAnimationFrame(raf)
    ro.disconnect()
    parent.removeEventListener('pointermove', onMove)
    parent.removeEventListener('pointerleave', onLeave)
    document.removeEventListener('visibilitychange', onVis)
  }
})

onUnmounted(() => cleanup?.())
</script>

<template>
  <canvas ref="canvas" class="absolute inset-0 pointer-events-none" aria-hidden="true" />
</template>
