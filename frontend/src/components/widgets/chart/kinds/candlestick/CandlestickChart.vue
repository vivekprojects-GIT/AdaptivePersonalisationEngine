<script setup lang="ts">
import { ref } from 'vue'
import ChartCard from '../../ChartCard.vue'
import { useEChart } from '../../useEChart'
import { candlestickOption } from './option'
import type { ChartSpec } from '@/lib/echartsOption'

const props = defineProps<{ title?: string; chart: ChartSpec }>()
const isDark = () => typeof matchMedia !== 'undefined' && matchMedia('(prefers-color-scheme: dark)').matches
const rootEl = ref<HTMLDivElement | null>(null)
const { toPng } = useEChart(rootEl, () => candlestickOption(props.chart, isDark()), () => props.chart)
</script>

<template>
  <ChartCard :title="title" @png="toPng(title || 'candlestick')">
    <div ref="rootEl" class="w-full h-[clamp(260px,40vh,400px)] min-h-[240px]" />
  </ChartCard>
</template>
