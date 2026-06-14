<script setup lang="ts">
import { ref } from 'vue'
import 'echarts-gl' // registers 3D series: scatter3D / bar3D / line3D
import ChartCard from '../../ChartCard.vue'
import { useEChart } from '../../useEChart'
import { threeDOption } from './option'
import type { ChartSpec } from '@/lib/echartsOption'

const props = defineProps<{ title?: string; chart: ChartSpec }>()
const isDark = () => typeof matchMedia !== 'undefined' && matchMedia('(prefers-color-scheme: dark)').matches
const rootEl = ref<HTMLDivElement | null>(null)
const { toPng } = useEChart(rootEl, () => threeDOption(props.chart, isDark()), () => props.chart)
</script>

<template>
  <ChartCard :title="title" @png="toPng(title || 'chart-3d')">
    <div ref="rootEl" class="w-full h-[clamp(320px,52vh,520px)] min-h-[300px]" />
  </ChartCard>
</template>
