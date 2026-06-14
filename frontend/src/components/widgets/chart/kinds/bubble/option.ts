import type { EChartsOption } from 'echarts'
import { toNum, colorAt, type ChartSpec } from '@/lib/echartsOption'

/** Bubble option — x vs y with auto-scaled point size from [x, y, size] triples. */
export function bubbleOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const eb = (chart?.series || []).map((s, i) => ({
    name: s.name || `Series ${i + 1}`,
    type: 'scatter' as const,
    data: (Array.isArray(s.values) ? s.values : [])
      .filter((v) => Array.isArray(v) && (v as number[]).length >= 2)
      .map((v) => (v as number[]).map((x) => toNum(x) ?? 0)),
    itemStyle: { color: colorAt(i, (chart?.series || []).length), opacity: 0.65 },
  }))
  // Auto-scale bubble size to a fixed pixel range from the data's own min/max.
  const sizeVals = eb.flatMap((s) => s.data.map((d) => Math.abs(Number(d[2]) || 0))).filter((v) => v > 0)
  const rmin = sizeVals.length ? Math.sqrt(Math.min(...sizeVals)) : 0
  const rmax = sizeVals.length ? Math.sqrt(Math.max(...sizeVals)) : 1
  const MIN_PX = 10
  const MAX_PX = 46
  const symbolSize = (val: number[]) => {
    const v = Math.abs(Number(val?.[2]) || 0)
    if (!(v > 0) || rmax <= rmin) return 16
    const t = (Math.sqrt(v) - rmin) / (rmax - rmin)
    return MIN_PX + t * (MAX_PX - MIN_PX)
  }
  const ebSized = eb.map((s) => ({ ...s, symbolSize }))
  return {
    backgroundColor: 'transparent',
    textStyle: { color: tc, fontSize: 11 },
    tooltip: { trigger: 'item' },
    legend: eb.length > 1 ? { bottom: 0, textStyle: { color: tc, fontSize: 10 } } : undefined,
    grid: { left: 48, right: 24, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: 'value', name: chart?.x_label || '', nameLocation: 'middle', nameGap: 26, splitLine: { lineStyle: { opacity: 0.2 } } },
    yAxis: { type: 'value', name: chart?.y_label || '', nameLocation: 'middle', nameGap: 36, splitLine: { lineStyle: { opacity: 0.2 } } },
    series: ebSized,
  }
}
