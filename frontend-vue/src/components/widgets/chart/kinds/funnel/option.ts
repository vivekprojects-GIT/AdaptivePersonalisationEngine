import type { EChartsOption } from 'echarts'
import { pieData, colorAt, makeFmtVal, type ChartSpec } from '@/lib/echartsOption'

/** Funnel option — composition as descending stages. */
export function funnelOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const fmtVal = makeFmtVal(chart)
  const d = pieData(chart)
  return {
    animation: true,
    backgroundColor: 'transparent',
    textStyle: { color: tc, fontSize: 11 },
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => p.name + ': ' + fmtVal(p.value) + (p.percent != null ? ' (' + p.percent + '%)' : ''),
    },
    legend: { bottom: 0, textStyle: { color: tc, fontSize: 10 } },
    series: [
      {
        type: 'funnel',
        left: '10%',
        right: '10%',
        top: 20,
        bottom: 40,
        sort: 'descending',
        gap: 2,
        label: { show: true, position: 'inside', fontSize: 10, color: '#fff', formatter: (p: any) => p.name + ': ' + fmtVal(p.value) },
        data: d.map((x, i) => ({ ...x, itemStyle: { color: colorAt(i, d.length) } })),
      },
    ],
  }
}
