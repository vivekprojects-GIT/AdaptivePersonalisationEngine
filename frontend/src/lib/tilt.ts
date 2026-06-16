import type { Directive } from 'vue'

// v-tilt — cursor-follow 3D tilt, like the hero cards: the element rotates
// toward the pointer and eases back on leave. Usage: `v-tilt` or `v-tilt="10"`
// (max degrees). Respects prefers-reduced-motion. Put it on an INNER wrapper,
// not on elements that already animate `transform` (e.g. .scrolly-depth).
type El = HTMLElement & { __tilt?: () => void }

export const vTilt: Directive<El, number | { max?: number } | void> = {
  mounted(el, binding) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const max = typeof binding.value === 'number' ? binding.value : (binding.value?.max ?? 8)
    el.style.transition = 'transform 280ms cubic-bezier(0.16, 1, 0.3, 1)'
    el.style.transformStyle = 'preserve-3d'
    let raf = 0
    const onMove = (e: PointerEvent) => {
      const r = el.getBoundingClientRect()
      const px = (e.clientX - r.left) / r.width - 0.5
      const py = (e.clientY - r.top) / r.height - 0.5
      cancelAnimationFrame(raf)
      raf = requestAnimationFrame(() => {
        el.style.transform = `perspective(1100px) rotateX(${(-py * max).toFixed(2)}deg) rotateY(${(px * max).toFixed(2)}deg)`
      })
    }
    const reset = () => {
      cancelAnimationFrame(raf)
      el.style.transform = 'perspective(1100px) rotateX(0deg) rotateY(0deg)'
    }
    el.addEventListener('pointermove', onMove)
    el.addEventListener('pointerleave', reset)
    el.__tilt = () => {
      el.removeEventListener('pointermove', onMove)
      el.removeEventListener('pointerleave', reset)
      cancelAnimationFrame(raf)
    }
  },
  unmounted(el) { el.__tilt?.() },
}
