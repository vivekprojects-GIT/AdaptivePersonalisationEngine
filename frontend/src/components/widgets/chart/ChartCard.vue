<script setup lang="ts">
// Shared chart "card" shell (border + header + PNG button) so each per-plot
// component stays tiny. The plot's canvas goes in the default slot.
import { ref } from 'vue'
import { ArrowDownTrayIcon } from '@/components/icons'

withDefaults(defineProps<{ title?: string; showPng?: boolean }>(), { showPng: true })
defineEmits<{ (e: 'png'): void }>()
const hovered = ref(false)
</script>

<template>
  <div
    class="card-sheen rounded-xl border bg-card overflow-hidden transition-all duration-300 hover:-translate-y-px"
    :style="{ boxShadow: hovered ? 'var(--shadow-md)' : 'var(--shadow-sm)' }"
    @mouseenter="hovered = true"
    @mouseleave="hovered = false"
  >
    <div class="px-3.5 py-2 border-b border-border/70 flex items-center justify-between gap-2 bg-muted/30">
      <span class="inline-flex items-center gap-2 min-w-0">
        <span class="h-1.5 w-1.5 rounded-full shrink-0 bg-gradient-to-r from-primary to-accent" />
        <span class="text-xs font-semibold tracking-wide truncate">{{ title }}</span>
      </span>
      <button
        v-if="showPng"
        type="button"
        class="shrink-0 inline-flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground border rounded-md px-2 py-0.5 transition cursor-pointer hover:bg-background/80"
        title="Download chart as PNG"
        @click="$emit('png')"
      >
        <ArrowDownTrayIcon class="h-3 w-3" /> PNG
      </button>
    </div>
    <slot />
  </div>
</template>
