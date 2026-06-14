import type { EChartsOption } from 'echarts'
import { toNum, type ChartSpec } from '@/lib/echartsOption'

/** Themeriver / streamgraph — categories over time. */
export function themeriverOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const cats = chart?.x_categories || []
  const data: [string, number, string][] = []
  for (const s of chart?.series || []) {
    const name = s.name || 'series'
    const vals = Array.isArray(s.values) ? s.values : []
    vals.forEach((v, i) => {
      const t = cats[i] ?? String(i)
      data.push([t, toNum(Array.isArray(v) ? v[1] : v) ?? 0, name])
    })
  }
  return {
    backgroundColor: 'transparent',
    textStyle: { color: tc, fontSize: 11 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'line' } },
    legend: { bottom: 0, textStyle: { color: tc, fontSize: 10 } },
    singleAxis: { type: 'category', data: cats, top: 20, bottom: 56, axisLabel: { fontSize: 10 } },
    series: [{ type: 'themeRiver', data, label: { show: false }, emphasis: { focus: 'self' } }],
  } as EChartsOption
}
