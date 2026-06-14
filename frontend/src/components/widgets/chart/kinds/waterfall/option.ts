import type { EChartsOption } from 'echarts'
import { pieData, POSITIVE, NEGATIVE, type ChartSpec } from '@/lib/echartsOption'

/** Waterfall option — running total walk (P&L bridge / cash-flow). */
export function waterfallOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const pts = pieData(chart)
  const cats = pts.map((p) => p.name)
  const base: (number | string)[] = []
  const inc: (number | string)[] = []
  const dec: (number | string)[] = []
  let run = 0
  for (const p of pts) {
    const v = Number(p.value) || 0
    if (v >= 0) {
      base.push(run)
      inc.push(v)
      dec.push('-')
    } else {
      base.push(run + v)
      inc.push('-')
      dec.push(-v)
    }
    run += v
  }
  return {
    backgroundColor: 'transparent',
    textStyle: { color: tc, fontSize: 11 },
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 16, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: 'category', data: cats, axisLabel: { fontSize: 10, rotate: cats.length > 6 ? 30 : 0 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { opacity: 0.2 } } },
    series: [
      { type: 'bar', stack: 'wf', itemStyle: { color: 'transparent' }, emphasis: { itemStyle: { color: 'transparent' } }, data: base },
      { type: 'bar', stack: 'wf', name: 'Increase', itemStyle: { color: POSITIVE }, data: inc },
      { type: 'bar', stack: 'wf', name: 'Decrease', itemStyle: { color: NEGATIVE }, data: dec },
    ],
  }
}
