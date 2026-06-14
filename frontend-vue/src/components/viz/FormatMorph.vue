<script setup lang="ts">
/** FormatMorph, the product demoing itself: the SAME answer auto-morphs
 *  between formats (table → bullets → one-liner) every few seconds, with the
 *  APE strategy chip updating in sync. Pauses under reduced motion. */
import { onMounted, onUnmounted, ref } from 'vue'
import { BoltIcon } from '@/components/icons'

const formats = ['comparison table', 'bullet summary', 'one liner'] as const
const idx = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  timer = setInterval(() => {
    idx.value = (idx.value + 1) % formats.length
  }, 2600)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="rounded-2xl border bg-card p-4 w-full">
    <div class="flex items-center gap-1.5 mb-2.5">
      <div class="text-[10px] text-muted-foreground">Assistant</div>
      <Transition name="morph-chip" mode="out-in">
        <div :key="idx" class="ape-chip ape-chip-strategy">
          <BoltIcon class="h-3 w-3" />
          {{ formats[idx] }}
        </div>
      </Transition>
      <div class="ape-chip">Decision</div>
    </div>

    <div class="relative h-[84px]">
      <Transition name="morph-body" mode="out-in">
        <!-- table -->
        <div v-if="idx === 0" key="t" class="grid grid-cols-3 gap-1.5">
          <div class="h-2.5 rounded bg-primary/40" /><div class="h-2.5 rounded bg-muted" /><div class="h-2.5 rounded bg-muted" />
          <div class="h-2.5 rounded bg-muted" /><div class="h-2.5 rounded bg-primary/30" /><div class="h-2.5 rounded bg-muted" />
          <div class="h-2.5 rounded bg-muted" /><div class="h-2.5 rounded bg-muted" /><div class="h-2.5 rounded bg-primary/30" />
          <div class="h-2.5 rounded bg-primary/20" /><div class="h-2.5 rounded bg-muted" /><div class="h-2.5 rounded bg-muted" />
        </div>
        <!-- bullets -->
        <div v-else-if="idx === 1" key="b" class="space-y-2.5 pt-1">
          <div class="flex items-center gap-2"><div class="h-1.5 w-1.5 rounded-full bg-primary/70" /><div class="h-2.5 flex-1 rounded bg-muted" /></div>
          <div class="flex items-center gap-2"><div class="h-1.5 w-1.5 rounded-full bg-primary/70" /><div class="h-2.5 w-4/5 rounded bg-muted" /></div>
          <div class="flex items-center gap-2"><div class="h-1.5 w-1.5 rounded-full bg-primary/70" /><div class="h-2.5 w-3/5 rounded bg-muted" /></div>
        </div>
        <!-- one liner -->
        <div v-else key="o" class="pt-6">
          <div class="h-3 w-11/12 rounded bg-muted" />
          <div class="mt-3 text-[10px] text-muted-foreground">exactly one sentence, nothing else</div>
        </div>
      </Transition>
    </div>

    <!-- cycle dots -->
    <div class="flex items-center gap-1.5 mt-2">
      <span
        v-for="(f, i) in formats" :key="f"
        class="h-1 rounded-full transition-all duration-500"
        :class="i === idx ? 'w-5 bg-primary/80' : 'w-1.5 bg-muted-foreground/30'"
      />
      <span class="ml-auto text-[9px] uppercase tracking-wider text-muted-foreground/70">same answer · new shape</span>
    </div>
  </div>
</template>

<style scoped>
.morph-body-enter-active,
.morph-body-leave-active {
  transition: opacity 360ms cubic-bezier(0.22, 1, 0.36, 1), transform 360ms cubic-bezier(0.22, 1, 0.36, 1);
}
.morph-body-enter-from { opacity: 0; transform: translateY(10px) scale(0.97); }
.morph-body-leave-to { opacity: 0; transform: translateY(-10px) scale(0.97); }

.morph-chip-enter-active,
.morph-chip-leave-active {
  transition: opacity 240ms ease, transform 240ms ease;
}
.morph-chip-enter-from { opacity: 0; transform: translateY(5px); }
.morph-chip-leave-to { opacity: 0; transform: translateY(-5px); }
</style>
