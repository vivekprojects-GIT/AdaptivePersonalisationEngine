import type { EChartsOption } from 'echarts'
import { toNum, type ChartSpec } from '@/lib/echartsOption'

/** Boxplot option — distribution / quartiles per category. */
export function boxplotOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const cats = chart?.x_categories || []
  const data = (chart?.boxes || []).map((b) => (Array.isArray(b) ? b.slice(0, 5).map((v) => toNum(v) ?? 0) : []))
  return {
    backgroundColor: 'transparent',
    textStyle: { color: tc, fontSize: 11 },
    tooltip: { trigger: 'item' },
    grid: { left: 48, right: 16, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: 'category', data: cats, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', scale: true, splitLine: { lineStyle: { opacity: 0.2 } } },
    series: [{ type: 'boxplot', data, itemStyle: { color: 'rgba(59,130,246,0.25)', borderColor: '#3b82f6' } }],
  }
}
