<!--
  UseCaseGrid — reuses the StoryGrid tile-card format (light-blue gradient tile +
  headline + category), but for honest product content: the surfaces where APE
  reshapes answers. No customer logos or claims.
-->
<script setup lang="ts">
const cases = [
  { tag: 'support',   label: 'Support',    head: 'Skimmers get the one-line fix; power users get every step' },
  { tag: 'sales · revops', label: 'Sales', head: 'Reps get the verdict, ops get the side-by-side table' },
  { tag: 'analytics · bi', label: 'Analytics', head: 'Visual thinkers get the chart; readers get the takeaway' },
  { tag: 'enablement', label: 'Onboarding', head: 'New hires get step-by-step; veterans get the TL;DR' },
  { tag: 'agents · copilots', label: 'Agents', head: 'Every tool result reshaped to how that user reads' },
  { tag: 'rag · search', label: 'Knowledge', head: 'Retrieved answers delivered in each reader’s shape' },
]
</script>

<template>
  <section class="max-w-7xl mx-auto px-5 lg:px-8 py-16 lg:py-24">
    <div class="flex items-end justify-between gap-6 mb-10" v-reveal>
      <h2 class="text-2xl sm:text-3xl lg:text-[40px] font-semibold leading-[1.1]">
        One engine, every surface.
        <span class="text-muted-foreground block text-base lg:text-lg font-normal mt-2">
          Drop APE wherever answers reach people — it reshapes each reply to the reader.
        </span>
      </h2>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5" v-reveal>
      <article v-for="(c, i) in cases" :key="i" class="story" :style="{ '--d': i * 60 + 'ms' }">
        <div class="tile">
          <span class="logo-ph">{{ c.label }}</span>
          <span class="go" aria-hidden="true">→</span>
        </div>
        <h3 class="head">{{ c.head }}</h3>
        <p class="meta">{{ c.tag }}</p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.story { display: flex; flex-direction: column; }
.tile {
  position: relative; aspect-ratio: 4 / 3; border-radius: 18px; overflow: hidden;
  display: grid; place-items: center;
  background: linear-gradient(155deg, #211f44 0%, #16182e 55%, #0e1020 100%);
  border: 1px solid var(--border);
  transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
.story:hover .tile { transform: translateY(-4px); box-shadow: 0 24px 50px -24px rgba(63, 99, 196, 0.45); }
.logo-ph {
  font-family: 'Geist', sans-serif; font-weight: 600; font-size: 26px; letter-spacing: -0.03em;
  color: color-mix(in oklab, var(--accent-strong) 78%, transparent);
}
.go {
  position: absolute; top: 12px; right: 12px; width: 30px; height: 30px;
  display: grid; place-items: center; border-radius: 999px;
  background: var(--foreground); color: #fff; font-size: 14px;
  opacity: 0; transform: translateY(-4px); transition: opacity 0.3s ease, transform 0.3s ease;
}
.story:hover .go { opacity: 1; transform: translateY(0); }
.head { margin-top: 16px; font-size: 18px; font-weight: 600; letter-spacing: -0.02em; line-height: 1.3; }
.meta { margin-top: 6px; font: 500 11px/1 'JetBrains Mono', monospace; letter-spacing: 0.05em; color: var(--muted-foreground); text-transform: uppercase; }
</style>
