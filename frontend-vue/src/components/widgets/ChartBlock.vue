<script setup lang="ts">
import ChartHost from '@/components/widgets/chart/ChartHost.vue'

const props = defineProps<{ block: { title?: string; chart?: Record<string, unknown> } }>()
</script>

<template>
  <ChartHost :title="props.block.title" :chart="(props.block.chart as any) || {}" />
</template>
