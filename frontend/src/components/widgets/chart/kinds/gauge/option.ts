import type { EChartsOption } from 'echarts'
import { gaugeData, type ChartSpec } from '@/lib/echartsOption'

/** Gauge option — a single headline value against a max. */
export function gaugeOption(chart: ChartSpec, dark: boolean, title = ''): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const g = gaugeData(chart, title)
  return {
    animation: true,
    backgroundColor: 'transparent',
    series: [
      {
        type: 'gauge',
        min: 0,
        max: g.max,
        progress: { show: true, width: 14 },
        axisLine: { lineStyle: { width: 14 } },
        axisLabel: { fontSize: 9, color: tc },
        detail: { valueAnimation: true, fontSize: 22, color: tc, formatter: '{value}' },
        data: [{ value: Number(g.value.toFixed(2)), name: g.name }],
        title: { fontSize: 11, color: tc },
      },
    ],
  }
}
