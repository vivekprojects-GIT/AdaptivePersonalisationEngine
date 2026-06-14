import type { EChartsOption } from 'echarts'
import { cartesianSeries, colorAt, type ChartSpec } from '@/lib/echartsOption'

/** Parallel coordinates — one polyline per series across the x_categories dimensions. */
export function parallelOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const s = cartesianSeries(chart)
  const dims = chart?.x_categories || s[0]?.points.map((_, i) => `Dim ${i + 1}`) || []
  return {
    animation: true,
    backgroundColor: 'transparent',
    textStyle: { color: tc, fontSize: 11 },
    tooltip: {},
    legend: s.length > 1 ? { bottom: 0, textStyle: { color: tc, fontSize: 10 } } : undefined,
    parallelAxis: dims.map((name, i) => ({ dim: i, name, nameTextStyle: { fontSize: 10 } })),
    parallel: { left: 60, right: 40, top: 30, bottom: 40 },
    series: s.map((ss, i) => ({
      type: 'parallel',
      name: ss.name,
      lineStyle: { width: 2, opacity: 0.6, color: ss.color || colorAt(i) },
      data: [ss.points.map((p) => p[1] ?? 0)],
    })),
  } as EChartsOption
}
