import type { EChartsOption } from 'echarts'
import { radarData, colorAt, type ChartSpec } from '@/lib/echartsOption'

/** Radar option — compare items across several dimensions. */
export function radarOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const { indicator, data } = radarData(chart)
  return {
    animation: true,
    backgroundColor: 'transparent',
    textStyle: { color: tc, fontSize: 11 },
    tooltip: { trigger: 'item' },
    legend: data.length > 1 ? { bottom: 0, textStyle: { color: tc, fontSize: 10 } } : undefined,
    radar: { indicator, axisName: { fontSize: 10, color: tc }, splitLine: { lineStyle: { opacity: 0.3 } } },
    series: [
      {
        type: 'radar',
        data: data.map((s, i) => ({
          ...s,
          areaStyle: { opacity: 0.12, color: colorAt(i, data.length) },
          lineStyle: { color: colorAt(i, data.length) },
          itemStyle: { color: colorAt(i, data.length) },
        })),
      },
    ],
  }
}
