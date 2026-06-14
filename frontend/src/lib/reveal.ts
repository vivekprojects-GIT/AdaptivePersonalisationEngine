import type { Directive } from 'vue'

/**
 * v-reveal — scroll-triggered entrance animation.
 *
 * Elements start hidden (`reveal-init`) and gain `is-revealed` the first time
 * they enter the viewport, driving a CSS transition (see globals.css).
 *
 *   <section v-reveal>            → fade+rise when scrolled into view
 *   <div v-reveal="120">          → same, with a 120ms delay (for stagger)
 *
 * Implementation note: this deliberately does NOT use IntersectionObserver —
 * some embedded webviews report isIntersecting=false for fully visible
 * elements, which would leave sections permanently hidden. A rAF-throttled
 * scroll check on getBoundingClientRect is universally reliable and cheap
 * (the pending set only shrinks; listeners detach when it empties).
 *
 * Reduced motion → elements are never hidden at all.
 */

const pending = new Map<HTMLElement, number>()
let raf = 0
let timer = 0
let listening = false

function reveal(el: HTMLElement, delay: number) {
  el.style.transitionDelay = delay ? `${delay}ms` : ''
  el.classList.add('is-revealed')
  pending.delete(el)
}

function check() {
  if (raf) cancelAnimationFrame(raf)
  if (timer) clearTimeout(timer)
  raf = 0
  timer = 0
  if (!pending.size) return detach()
  // Reveal anything whose top edge is above 92% of the viewport — including
  // elements already scrolled past, so nothing is ever invisible on scroll-up.
  const limit = window.innerHeight * 0.92
  for (const [el, delay] of pending) {
    if (el.getBoundingClientRect().top < limit) reveal(el, delay)
  }
  if (!pending.size) detach()
}

function schedule() {
  if (raf || timer) return
  // rAF for smoothness, plus a timeout fallback for environments that
  // throttle rAF (backgrounded webviews) — whichever fires first runs check.
  raf = requestAnimationFrame(check)
  timer = window.setTimeout(check, 120)
}

function attach() {
  if (listening) return
  listening = true
  window.addEventListener('scroll', schedule, { passive: true })
  window.addEventListener('resize', schedule, { passive: true })
}

function detach() {
  if (!listening) return
  listening = false
  window.removeEventListener('scroll', schedule)
  window.removeEventListener('resize', schedule)
}

export const vReveal: Directive<HTMLElement, number | undefined> = {
  mounted(el, binding) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    el.classList.add('reveal-init')
    pending.set(el, Number(binding.value) || 0)
    attach()
    // Initial check after layout settles (route transitions included).
    requestAnimationFrame(schedule)
  },
  beforeUnmount(el) {
    pending.delete(el)
    if (!pending.size) detach()
  },
}
