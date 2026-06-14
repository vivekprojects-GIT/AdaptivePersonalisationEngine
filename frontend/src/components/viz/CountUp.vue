<script setup lang="ts">
/** CountUp — a number that counts from 0 to `end` the first time it scrolls
 *  into view. Ease-out cubic so it lands softly. Reduced-motion → static. */
import { onMounted, onUnmounted, ref } from 'vue'

const props = withDefaults(
  defineProps<{ end: number; prefix?: string; suffix?: string; duration?: number }>(),
  { prefix: '', suffix: '', duration: 1200 },
)

const el = ref<HTMLElement | null>(null)
const display = ref('0')
let raf = 0
let io: IntersectionObserver | null = null

function run() {
  const t0 = performance.now()
  const tick = (t: number) => {
    const p = Math.min(1, (t - t0) / props.duration)
    const eased = 1 - Math.pow(1 - p, 3)
    display.value = String(Math.round(props.end * eased))
    if (p < 1) raf = requestAnimationFrame(tick)
  }
  raf = requestAnimationFrame(tick)
}

onMounted(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    display.value = String(props.end)
    return
  }
  io = new IntersectionObserver(
    (entries) => {
      if (entries.some((e) => e.isIntersecting)) {
        run()
        io?.disconnect()
        io = null
      }
    },
    { threshold: 0.4 },
  )
  if (el.value) io.observe(el.value)
})

onUnmounted(() => {
  cancelAnimationFrame(raf)
  io?.disconnect()
})
</script>

<template>
  <span ref="el" class="tabular-nums">{{ prefix }}{{ display }}{{ suffix }}</span>
</template>
