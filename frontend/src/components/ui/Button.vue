<script setup lang="ts">
import { computed, useAttrs } from 'vue'
import { RouterLink } from 'vue-router'
import { cn } from '@/lib/utils'

type Variant = 'default' | 'secondary' | 'destructive' | 'outline' | 'ghost'
type Size = 'sm' | 'md' | 'lg' | 'icon'

const props = withDefaults(
  defineProps<{
    variant?: Variant
    size?: Size
    type?: 'button' | 'submit' | 'reset'
    disabled?: boolean
    /** When set, the button renders as a router link (a real <a>, never a
     *  <button> nested in an <a> — which is invalid HTML and breaks clicks). */
    to?: string
  }>(),
  {
    variant: 'default',
    size: 'md',
    type: 'button',
    disabled: false,
  },
)

const attrs = useAttrs()

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'secondary':
      return 'bg-secondary/90 text-secondary-foreground hover:bg-secondary shadow-sm shadow-slate-900/5'
    case 'destructive':
      return 'bg-destructive text-destructive-foreground hover:bg-destructive/92 shadow-sm shadow-red-600/20'
    case 'outline':
      return 'border border-red-400/25 bg-card/40 backdrop-blur-sm text-foreground hover:bg-red-500/12 hover:border-red-400/55 hover:text-[#ffffff] hover:shadow-[0_6px_22px_-10px_rgba(255,6,10,0.5)]'
    case 'ghost':
      return 'text-foreground/90 hover:text-foreground hover:bg-accent/14'
    case 'default':
    default:
      return 'btn-premium border border-black/10'
  }
})

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'h-8 px-3 text-xs rounded-lg'
    case 'lg':
      return 'h-11 px-5 text-sm rounded-xl'
    case 'icon':
      return 'h-9 w-9 p-0 rounded-lg'
    case 'md':
    default:
      return 'h-9 px-4 text-sm rounded-lg'
  }
})

const classes = computed(() =>
  cn(
    'inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium select-none',
    'transition-all duration-200 ease-[cubic-bezier(0.16,1,0.3,1)] motion-safe:hover:-translate-y-px active:scale-[0.97] active:translate-y-0 cursor-pointer',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/85 focus-visible:ring-offset-2 focus-visible:ring-offset-background',
    'disabled:pointer-events-none disabled:opacity-50 disabled:saturate-75 disabled:shadow-none',
    '[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg]:h-4 [&_svg]:w-4',
    sizeClasses.value,
    variantClasses.value,
    (attrs.class as string) || '',
  ),
)
</script>

<template>
  <RouterLink v-if="to" :to="to" :class="classes">
    <slot />
  </RouterLink>
  <button v-else :type="props.type" :disabled="props.disabled" :class="classes">
    <slot />
  </button>
</template>
