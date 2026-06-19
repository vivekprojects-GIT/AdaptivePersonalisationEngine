<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  subtext?: string
  tone?: 'success' | 'warning' | 'danger' | 'info' | 'default'
}>()

// Semantic status tones stay conventional (success green, warning amber) — they
// signal meaning, not brand; only the brand accent is blue.
const toneToText: Record<string, string> = {
  success: 'text-emerald-600 dark:text-emerald-300',
  warning: 'text-amber-600 dark:text-amber-300',
  danger: 'text-rose-600 dark:text-rose-300',
  info: 'text-red-600 dark:text-red-300',
  default: 'text-foreground',
}
</script>

<template>
  <div
    class="rounded-lg border bg-card/70 glass-panel px-3 py-2.5 shadow-sm transition-[transform,box-shadow,border-color] duration-300 motion-safe:hover:-translate-y-0.5 hover:shadow-md hover:border-red-400/30"
  >
    <div class="text-[10px] uppercase tracking-wide text-muted-foreground">{{ label }}</div>
    <div class="text-xl font-semibold mt-0.5 leading-tight" :class="toneToText[tone || 'default']">{{ value }}</div>
    <div v-if="subtext" class="text-[11px] text-muted-foreground mt-0.5">{{ subtext }}</div>
    <div
      v-if="tone && tone !== 'default'"
      class="mt-2 h-1 rounded-full bg-background/60 overflow-hidden border border-border/60"
    >
      <div
        class="h-full bg-gradient-to-r opacity-90 transition-all duration-700"
        :class="{
          'from-emerald-500/90 to-emerald-300/70': tone === 'success',
          'from-amber-500/90 to-amber-300/70': tone === 'warning',
          'from-rose-500/90 to-rose-300/70': tone === 'danger',
          'from-red-500/90 to-red-300/70': tone === 'info',
        }"
        style="width: 70%"
      />
    </div>
  </div>
</template>

