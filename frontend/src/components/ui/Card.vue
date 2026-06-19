<script setup lang="ts">
import { cn } from '@/lib/utils'

defineProps<{
  class?: string
}>()
</script>

<template>
  <div
    :class="
      cn(
        // Default glossy/glass panel styling across the app.
        'rounded-xl border text-card-foreground shadow-[var(--shadow-sm)] transition-[transform,box-shadow,border-color] duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] motion-safe:hover:-translate-y-0.5 hover:shadow-[var(--shadow-lg)] hover:border-red-400/30 glass-panel',
        $attrs.class as string,
      )
    "
  >
    <slot />
  </div>
</template>

