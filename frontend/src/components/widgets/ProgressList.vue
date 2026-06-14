<script setup lang="ts">
import ProgressBar from '@/components/premium/ProgressBar.vue'

// SEMANTIC tone from the LLM (meaning only). The component maps meaning -> color;
// the LLM never picks a color. Back-compat: old color-named tones still resolve.
type Tone = 'default' | 'success' | 'warning' | 'danger' | 'info'
type BarTone = 'emerald' | 'amber' | 'red' | 'cyan' | 'indigo'

const TONE_TO_COLOR: Record<string, BarTone> = {
  default: 'indigo',
  success: 'emerald',
  warning: 'amber',
  danger: 'red',
  info: 'cyan',
  // legacy color-named tones map to themselves
  emerald: 'emerald',
  amber: 'amber',
  red: 'red',
  cyan: 'cyan',
  indigo: 'indigo',
}

function barTone(tone?: string): BarTone {
  return TONE_TO_COLOR[String(tone || 'default')] || 'indigo'
}

defineProps<{
  block: { items?: { label?: string; value?: number; max?: number; tone?: Tone }[] }
}>()
</script>

<template>
  <div class="space-y-3">
    <div v-for="(it, i) in block.items || []" :key="i">
      <div class="flex items-center justify-between text-xs mb-1">
        <span class="text-muted-foreground">{{ it.label }}</span>
        <span class="font-medium">{{ it.value }}{{ !it.max || it.max === 100 ? '%' : '' }}</span>
      </div>
      <ProgressBar :value="Number(it.value) || 0" :max="it.max ?? 100" :tone="barTone(it.tone)" />
    </div>
  </div>
</template>
