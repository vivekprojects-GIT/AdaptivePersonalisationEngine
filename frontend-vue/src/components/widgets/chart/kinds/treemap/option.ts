import type { EChartsOption } from 'echarts'
import { pieData, colorAt, makeFmtVal, toNum, type ChartSpec } from '@/lib/echartsOption'

/** Treemap / sunburst option — composition / hierarchy by area. */
export function treemapOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const fmtVal = makeFmtVal(chart)
  const isSunburst = String(chart?.kind || '').toLowerCase() === 'sunburst'
  const src = chart?.items?.length
    ? chart.items.map((it, i) => ({ name: it.label || it.name || `Item ${i + 1}`, value: toNum(it.value) ?? 0 }))
    : pieData(chart)
  const d = src.map((x, i) => ({ ...x, itemStyle: { color: colorAt(i, src.length) } }))
  return {
    backgroundColor: 'transparent',
    textStyle: { color: tc, fontSize: 11 },
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => p.name + ': ' + fmtVal(p.value) + (p.percent != null ? ' (' + p.percent + '%)' : ''),
    },
    series: [
      isSunburst
        ? { type: 'sunburst', data: d, radius: [0, '92%'], label: { fontSize: 10 } }
        : {
            type: 'treemap',
            data: d,
            breadcrumb: { show: false },
            roam: false,
            label: { fontSize: 11, formatter: (p: any) => p.name + '\n' + fmtVal(p.value) },
          },
    ],
  }
}
