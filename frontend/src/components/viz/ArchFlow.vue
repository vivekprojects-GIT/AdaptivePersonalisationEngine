<script setup lang="ts">
/** ArchFlow, an animated "where APE sits" architecture diagram for a
 *  RAG / agentic stack, in the product's design language.
 *
 *  Layout (1000×460 canvas):
 *    User → Orchestrator (intent · context · memory agents)
 *         → APE (format decision, the glowing one-call node)
 *         → Synthesizer LLM → Governed renderer → back to User
 *    RAG branch: Retriever ⇄ Vector store feeding the Synthesizer
 *    Tools row: queues / APIs / processors feeding the Orchestrator
 *
 *  Edges carry traveling signal pulses (same technique as NeuralBrain).
 *  Pure SVG + CSS, theme-aware via currentColor / CSS vars.
 */

type Node = {
  id: string
  x: number; y: number; w: number; h: number
  title: string
  sub?: string
  chips?: string[]
  hot?: boolean // APE, the highlighted node
}

const nodes: Node[] = [
  { id: 'user', x: 16, y: 168, w: 132, h: 96, title: 'User / Client', chips: ['chat', 'voice', 'dashboard'] },
  { id: 'orch', x: 204, y: 140, w: 178, h: 152, title: 'Agent Orchestrator', sub: 'your framework', chips: ['intent agent', 'context agent', 'memory agent'] },
  { id: 'tools', x: 204, y: 332, w: 178, h: 72, title: 'Tools · APIs · Queues', sub: 'parallel processors' },
  { id: 'rag', x: 440, y: 26, w: 150, h: 78, title: 'Retriever', sub: 'RAG pipeline' },
  { id: 'vec', x: 644, y: 26, w: 150, h: 78, title: 'Vector store', sub: 'embeddings' },
  { id: 'ape', x: 432, y: 162, w: 166, h: 108, title: 'APE', sub: 'format decision · reward', chips: ['one call · ~3 ms'], hot: true },
  { id: 'llm', x: 652, y: 158, w: 156, h: 116, title: 'Synthesizer LLM', sub: 'writes the content', chips: ['in APE’s shape'] },
  { id: 'render', x: 856, y: 168, w: 130, h: 96, title: 'Governed renderer', sub: 'text · tables · charts' },
]

const byId = Object.fromEntries(nodes.map((n) => [n.id, n]))

function edge(a: string, b: string, opts?: { fromSide?: 'r' | 'b' | 't'; toSide?: 'l' | 't' | 'b' }) {
  const A = byId[a]; const B = byId[b]
  const fs = opts?.fromSide ?? 'r'
  const ts = opts?.toSide ?? 'l'
  const p1 = fs === 'r' ? { x: A.x + A.w, y: A.y + A.h / 2 }
    : fs === 'b' ? { x: A.x + A.w / 2, y: A.y + A.h }
    : { x: A.x + A.w / 2, y: A.y }
  const p2 = ts === 'l' ? { x: B.x, y: B.y + B.h / 2 }
    : ts === 't' ? { x: B.x + B.w / 2, y: B.y }
    : { x: B.x + B.w / 2, y: B.y + B.h }
  const dx = Math.max(36, Math.abs(p2.x - p1.x) * 0.45)
  if (fs === 'b' || ts === 't' || fs === 't' || ts === 'b') {
    const dy = Math.max(28, Math.abs(p2.y - p1.y) * 0.5)
    const c1 = fs === 'b' ? { x: p1.x, y: p1.y + dy } : fs === 't' ? { x: p1.x, y: p1.y - dy } : { x: p1.x + dx, y: p1.y }
    const c2 = ts === 't' ? { x: p2.x, y: p2.y - dy } : ts === 'b' ? { x: p2.x, y: p2.y + dy } : { x: p2.x - dx, y: p2.y }
    return `M${p1.x},${p1.y} C${c1.x},${c1.y} ${c2.x},${c2.y} ${p2.x},${p2.y}`
  }
  return `M${p1.x},${p1.y} C${p1.x + dx},${p1.y} ${p2.x - dx},${p2.y} ${p2.x},${p2.y}`
}

/* Edges carry their endpoint ids so node hover can light up its own paths. */
const edges: Array<{ a: string; b: string; d: string; pulse: boolean; delay: number; dur: number }> = [
  { a: 'user', b: 'orch', d: edge('user', 'orch'), pulse: true, delay: 0, dur: 2.6 },
  { a: 'orch', b: 'ape', d: edge('orch', 'ape'), pulse: true, delay: 0.5, dur: 2.4 },
  { a: 'ape', b: 'llm', d: edge('ape', 'llm'), pulse: true, delay: 1.1, dur: 2.2 },
  { a: 'llm', b: 'render', d: edge('llm', 'render'), pulse: true, delay: 1.7, dur: 2.2 },
  { a: 'orch', b: 'rag', d: edge('orch', 'rag', { fromSide: 't', toSide: 'l' }), pulse: true, delay: 0.6, dur: 2.8 },
  { a: 'rag', b: 'vec', d: edge('rag', 'vec'), pulse: true, delay: 1.0, dur: 2.0 },
  { a: 'rag', b: 'llm', d: edge('rag', 'llm', { fromSide: 'b', toSide: 't' }), pulse: true, delay: 1.4, dur: 2.4 },
  { a: 'orch', b: 'tools', d: edge('orch', 'tools', { fromSide: 'b', toSide: 't' }), pulse: true, delay: 0.9, dur: 2.2 },
  // response returns to the user along the bottom
  { a: 'render', b: 'user', d: 'M856,250 C700,330 360,330 152,250', pulse: true, delay: 2.4, dur: 3.2 },
]

/* Hover focus: highlight a node's own edges, dim the rest. */
import { ref } from 'vue'
const active = ref<string | null>(null)
function edgeState(e: { a: string; b: string }) {
  if (!active.value) return ''
  return e.a === active.value || e.b === active.value ? 'af-focus' : 'af-dim'
}
</script>

<template>
  <figure class="m-0">
    <svg viewBox="0 0 1000 460" class="w-full h-auto" role="img" aria-label="Architecture: user to agent orchestrator, APE format decision, synthesizer LLM and governed renderer, with RAG retriever, vector store and tool queues">
      <defs>
        <radialGradient id="af-glow" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stop-color="#3b63c4" stop-opacity="0.22" />
          <stop offset="100%" stop-color="#3b63c4" stop-opacity="0" />
        </radialGradient>
      </defs>

      <!-- glow behind APE -->
      <ellipse cx="515" cy="216" rx="150" ry="105" fill="url(#af-glow)" />

      <!-- edges -->
      <g>
        <template v-for="(e, i) in edges" :key="i">
          <path :d="e.d" class="af-edge" :class="edgeState(e)" />
          <path
            v-if="e.pulse"
            :d="e.d"
            class="af-pulse"
            :class="edgeState(e)"
            :style="{ animationDelay: e.delay + 's', animationDuration: e.dur + 's' }"
          />
        </template>
      </g>

      <!-- nodes (hover to trace this node's signal paths) -->
      <g
        v-for="n in nodes" :key="n.id"
        class="af-group"
        :class="active && active !== n.id ? 'af-group-dim' : ''"
        @pointerenter="active = n.id"
        @pointerleave="active = null"
      >
        <rect
          :x="n.x" :y="n.y" :width="n.w" :height="n.h" rx="14"
          :class="n.hot ? 'af-node-hot' : 'af-node'"
        />
        <text :x="n.x + 14" :y="n.y + 26" class="af-title" :class="n.hot ? 'af-title-hot' : ''">{{ n.title }}</text>
        <text v-if="n.sub" :x="n.x + 14" :y="n.y + 43" class="af-sub">{{ n.sub }}</text>
        <g v-if="n.chips">
          <g v-for="(c, ci) in n.chips" :key="c">
            <rect
              :x="n.x + 12" :y="n.y + 52 + ci * 24" :width="n.w - 24" height="19" rx="9.5"
              class="af-chip" :class="n.hot ? 'af-chip-hot' : ''"
            />
            <text :x="n.x + n.w / 2" :y="n.y + 65 + ci * 24" text-anchor="middle" class="af-chip-text">{{ c }}</text>
          </g>
        </g>
      </g>

      <!-- return-path label -->
      <text x="500" y="345" text-anchor="middle" class="af-sub">response · in the learned shape, reactions become next-turn rewards</text>
    </svg>
    <figcaption class="sr-only">
      The user's message flows through your agent orchestrator; APE makes the single format decision;
      the synthesizer LLM writes content in that shape; the governed renderer returns it to the user,
      whose reaction becomes the next reward.
    </figcaption>
  </figure>
</template>

<style scoped>
.af-edge {
  fill: none;
  stroke: color-mix(in oklab, var(--foreground) 16%, transparent);
  stroke-width: 1.2;
}
.af-pulse {
  fill: none;
  stroke: var(--primary);
  stroke-width: 2;
  stroke-linecap: round;
  stroke-dasharray: 22 600;
  stroke-dashoffset: 622;
  animation: afTravel 2.4s linear infinite;
  opacity: 0.95;
}
@keyframes afTravel { to { stroke-dashoffset: 0; } }

.af-node {
  fill: color-mix(in oklab, var(--card) 92%, transparent);
  stroke: var(--border);
  stroke-width: 1;
}
.af-node-hot {
  fill: color-mix(in oklab, var(--primary) 14%, var(--card));
  stroke: color-mix(in oklab, var(--primary) 55%, transparent);
  stroke-width: 1.4;
}
.af-title {
  font-size: 14px;
  font-weight: 650;
  fill: var(--foreground);
}
.af-title-hot { fill: var(--primary); }
.af-sub {
  font-size: 10.5px;
  fill: var(--muted-foreground);
}
.af-chip {
  fill: color-mix(in oklab, var(--muted) 70%, transparent);
  stroke: var(--border);
  stroke-width: 0.8;
}
.af-chip-hot {
  fill: color-mix(in oklab, var(--primary) 16%, transparent);
  stroke: color-mix(in oklab, var(--primary) 40%, transparent);
}
.af-chip-text {
  font-size: 10px;
  fill: var(--muted-foreground);
}

/* Hover focus states */
.af-edge, .af-pulse { transition: opacity 240ms ease, stroke-width 240ms ease; }
.af-edge.af-focus { stroke: color-mix(in oklab, var(--primary) 60%, transparent); stroke-width: 1.8; }
.af-pulse.af-focus { stroke-width: 3; }
.af-edge.af-dim, .af-pulse.af-dim { opacity: 0.15; }
.af-group { cursor: pointer; transition: opacity 240ms ease; }
.af-group-dim { opacity: 0.45; }

@media (prefers-reduced-motion: reduce) {
  .af-pulse { animation: none; opacity: 0; }
}
</style>
