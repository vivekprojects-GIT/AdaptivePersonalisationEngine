import type { Directive } from 'vue'

/**
 * v-magnet — the element leans toward the cursor (max ~7px) and springs back
 * on leave. The classic premium-CTA micro-interaction: buttons feel alive
 * without being gimmicky. GPU transform only; disabled for touch pointers
 * and under prefers-reduced-motion.
 */
const handlers = new WeakMap<HTMLElement, { move: (e: PointerEvent) => void; leave: () => void }>()

export const vMagnet: Directive<HTMLElement> = {
  mounted(el) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    if (window.matchMedia('(pointer: coarse)').matches) return

    el.style.transition = 'transform 280ms cubic-bezier(0.22, 1, 0.36, 1)'
    el.style.willChange = 'transform'

    const move = (e: PointerEvent) => {
      const r = el.getBoundingClientRect()
      const dx = e.clientX - (r.left + r.width / 2)
      const dy = e.clientY - (r.top + r.height / 2)
      el.style.transform = `translate(${(dx * 0.18).toFixed(1)}px, ${(dy * 0.22).toFixed(1)}px)`
    }
    const leave = () => {
      el.style.transform = 'translate(0, 0)'
    }

    el.addEventListener('pointermove', move, { passive: true })
    el.addEventListener('pointerleave', leave, { passive: true })
    handlers.set(el, { move, leave })
  },
  beforeUnmount(el) {
    const h = handlers.get(el)
    if (h) {
      el.removeEventListener('pointermove', h.move)
      el.removeEventListener('pointerleave', h.leave)
      handlers.delete(el)
    }
  },
}
