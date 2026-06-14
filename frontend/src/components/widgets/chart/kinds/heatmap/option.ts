import type { EChartsOption } from 'echarts'
import { heatmapData, type ChartSpec } from '@/lib/echartsOption'

/** Heatmap option — a grid of values (correlation/confusion matrices). */
export function heatmapOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const { xs, ys, data, vmin, vmax } = heatmapData(chart)
  const absMax = Math.max(Math.abs(vmin), Math.abs(vmax)) || 1
  const symmetric = vmin < 0
  return {
    animation: true,
    backgroundColor: 'transparent',
    textStyle: { color: tc, fontSize: 11 },
    tooltip: {
      position: 'top',
      formatter: (p: any) => `${ys[p.value?.[1]] ?? ''} × ${xs[p.value?.[0]] ?? ''}: ${Number(p.value?.[2]).toFixed(2)}`,
    },
    grid: { left: 60, right: 20, top: 16, bottom: 64, containLabel: true },
    xAxis: { type: 'category', data: xs, splitArea: { show: true }, axisLabel: { fontSize: 10, rotate: xs.length > 5 ? 30 : 0 } },
    yAxis: { type: 'category', data: ys, splitArea: { show: true }, axisLabel: { fontSize: 10 } },
    visualMap: {
      min: symmetric ? -absMax : vmin,
      max: symmetric ? absMax : vmax,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      itemHeight: 80,
      textStyle: { color: tc, fontSize: 10 },
      inRange: { color: symmetric ? ['#ef4444', '#f8fafc', '#3b82f6'] : ['#dbeafe', '#3b82f6', '#1e3a8a'] },
    },
    series: [
      {
        type: 'heatmap',
        data,
        label: {
          show: xs.length <= 10 && ys.length <= 10,
          fontSize: 10,
          formatter: (p: any) => (typeof p.value?.[2] === 'number' ? p.value[2].toFixed(2) : ''),
        },
        emphasis: { itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.3)' } },
      },
    ],
  }
}
