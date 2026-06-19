<script setup lang="ts">
/** NeuralBrain, a stylized human brain rendered as a living neural network.
 *  Pure SVG + CSS: glowing nodes (neurons) and bright pulses traveling along
 *  synapse paths via stroke-dash animation. GPU-only, reduced-motion aware.
 *
 *  INTERACTIVE: the cursor excites nearby neurons, they swell and brighten
 *  as the pointer approaches, like touching a living tissue.
 *
 *  The geometry is hand-placed inside a brain silhouette (side profile,
 *  facing right) on a 360×300 canvas.
 */
import { ref } from 'vue'

// Neurons, clustered like cortical regions; a few labeled as "preference"
// nodes that glow in the accent color.
const nodes = [
  // frontal lobe
  { x: 246, y: 78 }, { x: 282, y: 102 }, { x: 262, y: 140 }, { x: 296, y: 150 },
  // parietal / top
  { x: 196, y: 56 }, { x: 150, y: 52 }, { x: 110, y: 72 },
  // temporal / center
  { x: 168, y: 116 }, { x: 210, y: 124 }, { x: 138, y: 142 }, { x: 188, y: 168 },
  // occipital / back
  { x: 82, y: 116 }, { x: 64, y: 158 }, { x: 96, y: 182 },
  // cerebellum / lower back
  { x: 120, y: 214 }, { x: 158, y: 206 },
  // brain stem area
  { x: 196, y: 218 }, { x: 232, y: 196 },
]

// Highlighted "preference" neurons (indices into nodes).
const hot = new Set([2, 8, 10, 13])

// Synapses, pairs of node indices. Pulses travel along a subset.
const edges: Array<[number, number, boolean]> = [
  [0, 1, true], [0, 4, false], [1, 3, false], [2, 3, true], [2, 8, true],
  [4, 5, true], [5, 6, false], [5, 7, true], [6, 11, true], [7, 8, true],
  [7, 9, false], [8, 10, true], [9, 12, false], [9, 13, true], [10, 15, true],
  [10, 17, false], [11, 12, true], [12, 13, false], [13, 14, true],
  [14, 15, false], [15, 16, true], [16, 17, true], [17, 2, true], [3, 17, false],
  [6, 9, true], [4, 8, false],
]

function d(a: { x: number; y: number }, b: { x: number; y: number }) {
  // Gentle curve: control point offset perpendicular-ish for an organic feel.
  const mx = (a.x + b.x) / 2 + (a.y - b.y) * 0.18
  const my = (a.y + b.y) / 2 + (b.x - a.x) * 0.18
  return `M${a.x},${a.y} Q${mx},${my} ${b.x},${b.y}`
}

/* Pointer excitation, convert client coords to viewBox space; neurons within
 * reach get an excitation factor 0..1 that drives radius + glow. */
const svgEl = ref<SVGSVGElement | null>(null)
const ptr = ref({ x: -999, y: -999 })

function onPointer(e: PointerEvent) {
  const el = svgEl.value
  if (!el) return
  const r = el.getBoundingClientRect()
  ptr.value = {
    x: ((e.clientX - r.left) / r.width) * 360,
    y: ((e.clientY - r.top) / r.height) * 300,
  }
}
function onPointerLeave() {
  ptr.value = { x: -999, y: -999 }
}
function excite(n: { x: number; y: number }) {
  const dx = n.x - ptr.value.x
  const dy = n.y - ptr.value.y
  const dist = Math.sqrt(dx * dx + dy * dy)
  return dist > 70 ? 0 : 1 - dist / 70
}
</script>

<template>
  <svg
    ref="svgEl"
    viewBox="0 0 360 300"
    class="w-full h-full"
    aria-hidden="true"
    @pointermove="onPointer"
    @pointerleave="onPointerLeave"
  >
    <defs>
      <radialGradient id="nb-glow" cx="50%" cy="42%" r="60%">
        <stop offset="0%" stop-color="#d10006" stop-opacity="0.16" />
        <stop offset="100%" stop-color="#d10006" stop-opacity="0" />
      </radialGradient>
      <filter id="nb-blur" x="-60%" y="-60%" width="220%" height="220%">
        <feGaussianBlur stdDeviation="2.2" />
      </filter>
    </defs>

    <!-- ambient glow behind the brain -->
    <ellipse cx="180" cy="140" rx="170" ry="135" fill="url(#nb-glow)" />

    <!-- brain silhouette (side profile, facing right) -->
    <path
      d="M312,142
         c6,-34 -12,-66 -44,-80
         c-12,-26 -44,-40 -76,-34
         c-26,-14 -62,-10 -82,8
         c-30,4 -52,28 -54,56
         c-18,22 -16,56 4,76
         c2,26 24,46 50,50
         c10,16 30,26 48,24
         c6,10 18,16 30,14
         c16,-2 26,-12 28,-26
         c20,2 38,-6 48,-22
         c26,-4 44,-22 48,-44
         Z"
      fill="none"
      stroke="color-mix(in oklab, var(--primary) 38%, transparent)"
      stroke-width="1.5"
      class="nb-outline"
    />

    <!-- synapses -->
    <g>
      <template v-for="([a, b, pulse], i) in edges" :key="i">
        <path :d="d(nodes[a], nodes[b])" class="nb-edge" />
        <path
          v-if="pulse"
          :d="d(nodes[a], nodes[b])"
          class="nb-pulse"
          :style="{ animationDelay: (i * 0.42) % 5 + 's', animationDuration: 2.6 + (i % 4) * 0.5 + 's' }"
        />
      </template>
    </g>

    <!-- neurons (cursor-excitable) -->
    <g>
      <template v-for="(n, i) in nodes" :key="'n' + i">
        <!-- halo -->
        <circle
          :cx="n.x" :cy="n.y"
          :r="(hot.has(i) ? 8 : 5.5) + excite(n) * 9"
          :class="hot.has(i) ? 'nb-halo-hot' : 'nb-halo'"
          filter="url(#nb-blur)"
          :style="{ animationDelay: (i * 0.35) % 3 + 's', opacity: excite(n) > 0 ? 0.95 : undefined }"
        />
        <!-- core -->
        <circle
          :cx="n.x" :cy="n.y"
          :r="(hot.has(i) ? 3.2 : 2.2) + excite(n) * 2.4"
          :class="[hot.has(i) ? 'nb-node-hot' : 'nb-node', excite(n) > 0.15 ? 'nb-excited' : '']"
        />
      </template>
    </g>
  </svg>
</template>

<style scoped>
.nb-edge {
  fill: none;
  stroke: color-mix(in oklab, var(--primary) 20%, transparent);
  stroke-width: 1;
}

/* A bright signal segment traveling along the synapse. */
.nb-pulse {
  fill: none;
  stroke: var(--primary);
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-dasharray: 14 220;
  stroke-dashoffset: 234;
  animation: nbTravel 3s linear infinite;
  opacity: 0.9;
}
@keyframes nbTravel {
  to { stroke-dashoffset: 0; }
}

.nb-node {
  fill: color-mix(in oklab, var(--foreground) 70%, transparent);
  transition: r 180ms cubic-bezier(0.16, 1, 0.3, 1);
}
.nb-node-hot {
  fill: var(--primary);
  transition: r 180ms cubic-bezier(0.16, 1, 0.3, 1);
}
.nb-excited { fill: var(--primary); }

.nb-halo {
  fill: color-mix(in oklab, var(--foreground) 25%, transparent);
  animation: nbBreath 3.2s ease-in-out infinite;
}
.nb-halo-hot {
  fill: color-mix(in oklab, var(--primary) 75%, transparent);
  animation: nbBreath 2.4s ease-in-out infinite;
}
@keyframes nbBreath {
  0%, 100% { opacity: 0.35; }
  50% { opacity: 0.9; }
}

.nb-outline {
  stroke-dasharray: 4 7;
  animation: nbDash 26s linear infinite;
}
@keyframes nbDash {
  to { stroke-dashoffset: -220; }
}

@media (prefers-reduced-motion: reduce) {
  .nb-pulse { animation: none; opacity: 0; }
  .nb-halo, .nb-halo-hot, .nb-outline { animation: none; }
}
</style>
