<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import 'echarts-gl' // registers 3D series: scatter3D / bar3D / line3D / surface
import { ArrowDownTrayIcon } from '@/components/icons'
import { buildEChartsOption, chartHasRenderableData, type ChartSpec } from '@/lib/echartsOption'
import { resolveCustomKind } from './kinds/registry'

const props = defineProps<{
  title?: string
  chart: ChartSpec
}>()

const kind = computed(() => String(props.chart?.kind || 'line').toLowerCase())
const chartSpec = computed(() => props.chart)

// Plug-in seam: if a per-plot custom component is registered for this kind, render
// THAT (it brings its own library/code); otherwise use the built-in ECharts engine.
const customComp = computed(() => resolveCustomKind(kind.value))

const rootEl = ref<HTMLDivElement | null>(null)
let inst: echarts.ECharts | null = null

const renderable = computed(() => chartHasRenderableData(props.chart))

function buildOption(): echarts.EChartsOption {
  const dark = typeof matchMedia !== 'undefined' && matchMedia('(prefers-color-scheme: dark)').matches
  return buildEChartsOption(props.chart, props.title || '', { dark })
}

let ro: ResizeObserver | null = null
let resizeRaf = 0

function resize() {
  if (resizeRaf) return
  resizeRaf = requestAnimationFrame(() => {
    resizeRaf = 0
    inst?.resize()
  })
}

function initChart() {
  if (!rootEl.value) return
  if (inst) {
    inst.dispose()
    inst = null
  }
  inst = echarts.init(rootEl.value, undefined, { renderer: 'canvas' })
  inst.setOption(buildOption(), true)
  if (!ro && typeof ResizeObserver !== 'undefined') {
    ro = new ResizeObserver(() => resize())
    ro.observe(rootEl.value)
  }
}

function refresh() {
  if (customComp.value) return // custom component renders itself
  nextTick(() => {
    if (!renderable.value) {
      inst?.dispose()
      inst = null
      return
    }
    if (!inst || !rootEl.value) {
      initChart()
      return
    }
    inst.setOption(buildOption(), true)
  })
}

function downloadPng() {
  if (!inst) return
  const dark = typeof matchMedia !== 'undefined' && matchMedia('(prefers-color-scheme: dark)').matches
  const url = inst.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: dark ? '#13151c' : '#ffffff' })
  const name =
    (props.title || 'chart').replace(/[^a-zA-Z0-9_-]+/g, '-').replace(/^-|-$/g, '').slice(0, 60) || 'chart'
  const a = document.createElement('a')
  a.href = url
  a.download = `${name}.png`
  document.body.appendChild(a)
  a.click()
  a.remove()
}

onMounted(() => {
  refresh()
  window.addEventListener('resize', resize)
})

onUnmounted(() => {
  window.removeEventListener('resize', resize)
  if (resizeRaf) cancelAnimationFrame(resizeRaf)
  ro?.disconnect()
  ro = null
  inst?.dispose()
  inst = null
})

watch(() => props.chart, refresh, { deep: true })
</script>

<template>
  <!-- Real, self-contained per-plot component renders its OWN card (header/style). -->
  <component :is="customComp" v-if="customComp" :title="title" :chart="chartSpec" />

  <!-- Built-in ECharts kinds share this shell + engine. -->
  <div
    v-else
    class="wsc-root rounded-xl border bg-card overflow-hidden shadow-sm transition-shadow duration-300 hover:shadow-md"
  >
    <div v-if="title || renderable" class="px-3 py-2 border-b flex items-center justify-between gap-2">
      <span class="text-xs font-medium truncate">{{ title }}</span>
      <button
        v-if="renderable"
        type="button"
        class="shrink-0 inline-flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground border rounded-md px-2 py-0.5 transition"
        title="Download chart as PNG"
        @click="downloadPng"
      >
        <ArrowDownTrayIcon class="h-3 w-3" /> PNG
      </button>
    </div>
    <div v-if="renderable" ref="rootEl" class="w-full h-[clamp(260px,40vh,400px)] min-h-[240px]" />
    <div v-else class="px-3 py-6 text-xs text-muted-foreground text-center">
      No renderable data for chart type "{{ kind }}".
    </div>
  </div>
</template>
