<!--
  MetricCards — Ramp-style stat cards (ref: their "$250K / 7-9% / 15 hrs" tiles),
  in the blue-on-lavender treatment. APE's own engine numbers — capability facts,
  not fabricated customer outcomes.
-->
<script setup lang="ts">
const metrics = [
  { num: '18',  unit: '',   cap: 'answer formats APE picks between, every turn' },
  { num: '5',   unit: '',   cap: 'intents classified before it ever answers' },
  { num: '~3',  unit: 'ms', cap: 'median time to choose a format' },
  { num: '1:1', unit: '',   cap: 'a learned answer-shape for every person' },
  { num: '0',   unit: '',   cap: 'prompts for you to rewrite — APE reshapes the reply' },
  { num: 'live', unit: '',  cap: 'every rating updates the bandit in real time' },
]
</script>

<template>
  <section class="max-w-7xl mx-auto px-5 lg:px-8 py-16 lg:py-24">
    <div class="max-w-2xl" v-reveal>
      <h2 class="text-2xl sm:text-3xl lg:text-[40px] font-semibold leading-[1.1]">
        The engine, by the numbers.
        <span class="text-muted-foreground">A response-format layer that classifies, picks, renders, and learns.</span>
      </h2>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-10">
      <div v-for="(m, i) in metrics" :key="i" class="metric" v-reveal="i * 70">
        <div class="m-num"><span class="n">{{ m.num }}</span><span v-if="m.unit" class="u">{{ m.unit }}</span></div>
        <p class="m-cap">{{ m.cap }}</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.metric {
  background: var(--accent-soft);
  border: 1px solid color-mix(in oklab, var(--accent) 22%, transparent);
  border-radius: 18px;
  padding: 24px;
  min-height: 184px;
  display: flex; flex-direction: column; justify-content: space-between;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.metric:hover {
  transform: translateY(-3px);
  box-shadow: 0 18px 40px -20px rgba(255, 6, 10, 0.4);
}
.m-num {
  display: flex; align-items: baseline; gap: 5px;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  color: var(--accent-strong);
}
.m-num .n { font-size: 52px; font-weight: 600; line-height: 1; letter-spacing: -0.04em; }
.m-num .u { font-size: 24px; font-weight: 500; color: color-mix(in oklab, var(--accent-strong) 75%, transparent); }
.m-cap { font-size: 14px; line-height: 1.45; color: var(--foreground); max-width: 240px; }
</style>
