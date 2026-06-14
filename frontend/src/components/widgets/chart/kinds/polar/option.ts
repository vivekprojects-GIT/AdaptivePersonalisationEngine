import type { EChartsOption } from 'echarts'
import { cartesianSeries, colorAt, type ChartSpec } from '@/lib/echartsOption'

/** Polar bar — categorical bars wrapped around a circle. */
export function polarOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const s = cartesianSeries(chart)
  const cats = chart?.x_categories || s[0]?.points.map((_, i) => `#${i + 1}`) || []
  return {
    animation: true,
    backgroundColor: 'transparent',
    textStyle: { color: tc, fontSize: 11 },
    tooltip: { trigger: 'item' },
    legend: s.length > 1 ? { bottom: 0, textStyle: { color: tc, fontSize: 10 } } : undefined,
    polar: { radius: ['12%', '72%'] },
    angleAxis: { type: 'category', data: cats, axisLabel: { fontSize: 10 } },
    radiusAxis: { axisLabel: { fontSize: 9 } },
    series: s.map((ss, i) => ({
      type: 'bar',
      coordinateSystem: 'polar',
      name: ss.name,
      data: ss.points.map((p) => p[1]),
      itemStyle: { color: ss.color || colorAt(i) },
    })),
  } as EChartsOption
}
