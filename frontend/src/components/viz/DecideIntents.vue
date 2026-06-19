<!--
  DecideIntents — the DECIDE model from the deck: every user question maps to one
  of six intents, and each intent wants a different shape of answer. Six cards
  spelling D·E·C·I·D·E, each with its question, the user's underlying need, and
  the format APE leans toward. Content sourced from the APE deck (slides 8–9).
-->
<script setup lang="ts">
type Intent = { letter: string; name: string; q: string; need: string; fmt: string }
const intents: Intent[] = [
  { letter: 'D', name: 'Decision',     q: 'Which one should I pick?', need: 'A clear recommendation', fmt: 'Decision card' },
  { letter: 'E', name: 'Explanation',  q: 'How does this work?',      need: 'A mental model',         fmt: 'Short paragraph · analogy' },
  { letter: 'C', name: 'Comparison',   q: 'How do these differ?',     need: 'A side-by-side view',    fmt: 'Comparison table' },
  { letter: 'I', name: 'Instructional', q: 'How do I do this?',       need: 'A step-by-step guide',   fmt: 'Numbered steps' },
  { letter: 'D', name: 'Definitional', q: 'What is this?',            need: 'A quick definition',     fmt: 'One-liner' },
  { letter: 'E', name: 'Evaluation',   q: 'Am I doing this right?',   need: 'Validation of a plan',   fmt: 'Affirm + calibrate' },
]
</script>

<template>
  <section class="max-w-7xl mx-auto px-5 lg:px-8 py-24">
    <div class="text-center max-w-2xl mx-auto mb-12" v-reveal>
      <span class="eyebrow">the decide model</span>
      <h2 class="mt-3 text-4xl lg:text-5xl font-semibold tracking-[-0.03em]">Six things users come to ask.</h2>
      <p class="mt-4 text-base lg:text-lg text-muted-foreground">
        Every question maps to one of six intents — and each one wants a different shape of answer.
        APE classifies the intent first, then picks the format that fits.
      </p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <article v-for="(it, i) in intents" :key="i" class="dcard glass-panel" v-reveal="i * 70">
        <div class="dcard-top">
          <span class="dletter">{{ it.letter }}</span>
          <span class="dname">{{ it.name }}</span>
        </div>
        <p class="dq">“{{ it.q }}”</p>
        <div class="dneed"><span class="dneed-k">needs</span>{{ it.need }}</div>
        <div class="dfmt">{{ it.fmt }}</div>
      </article>
    </div>

    <p class="text-center text-sm text-muted-foreground mt-8 max-w-xl mx-auto" v-reveal>
      Anything that doesn't fit these six is captured as <span class="text-foreground">“unmapped”</span> —
      a candidate for future learning.
    </p>
  </section>
</template>

<style scoped>
.dcard {
  position: relative; border: 1px solid var(--border); border-radius: 18px;
  padding: 20px; display: flex; flex-direction: column; gap: 10px;
  transition: transform 0.32s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.32s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.32s ease;
}
.dcard:hover { transform: translateY(-3px); box-shadow: var(--shadow-glow-accent); border-color: color-mix(in oklab, var(--accent) 45%, var(--border)); }

.dcard-top { display: flex; align-items: center; gap: 12px; }
.dletter {
  width: 40px; height: 40px; flex: none; display: grid; place-items: center;
  border-radius: 11px; font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 20px;
  color: var(--accent-strong);
  background: color-mix(in oklab, var(--accent) 14%, transparent);
  border: 1px solid color-mix(in oklab, var(--accent) 30%, transparent);
}
.dname { font-size: 17px; font-weight: 600; letter-spacing: -0.02em; }
.dq { font-size: 15px; color: var(--foreground); font-weight: 500; }
.dneed { font-size: 13px; color: var(--muted-foreground); }
.dneed-k {
  font: 600 9px/1 'JetBrains Mono', monospace; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--muted-foreground); margin-right: 8px; opacity: 0.8;
}
.dfmt {
  margin-top: 2px; align-self: flex-start;
  font-size: 11.5px; font-weight: 600; padding: 3px 9px; border-radius: 999px;
  color: var(--accent-strong);
  background: color-mix(in oklab, var(--accent) 12%, transparent);
  border: 1px solid color-mix(in oklab, var(--accent) 28%, transparent);
}
@media (prefers-reduced-motion: reduce) { .dcard:hover { transform: none; } }
</style>
