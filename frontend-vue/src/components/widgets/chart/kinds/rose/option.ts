import type { EChartsOption } from 'echarts'
import { pieData, colorAt, makeFmtVal, type ChartSpec } from '@/lib/echartsOption'

/** Nightingale rose ("pizza") — pie with variable-radius slices. */
export function roseOption(chart: ChartSpec, dark: boolean): EChartsOption {
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
        type: 'pie',
        radius: ['18%', '72%'],
        center: ['50%', '46%'],
        roseType: 'area',
        itemStyle: { borderRadius: 4 },
        data: d.map((x, i) => ({ ...x, itemStyle: { color: colorAt(i, d.length) } })),
        label: { fontSize: 10, color: tc, formatter: (p: any) => p.name + ': ' + (p.percent != null ? p.percent + '%' : fmtVal(p.value)) },
      },
    ],
  }
}
