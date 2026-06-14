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
        'rounded-xl border text-card-foreground shadow-sm transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/20 hover:border-teal-400/30 dark:hover:border-teal-400/25 bg-white/70 dark:bg-background/55 glass-panel',
        $attrs.class as string,
      )
    "
  >
    <slot />
  </div>
</template>

