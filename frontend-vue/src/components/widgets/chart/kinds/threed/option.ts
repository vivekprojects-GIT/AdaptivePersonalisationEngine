import type { EChartsOption } from 'echarts'
import { series3d, colorAt, type ChartSpec } from '@/lib/echartsOption'

/** 3D plots — scatter3d / bar3d / line3d (requires echarts-gl, imported by the component). */
export function threeDOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const k = String(chart?.kind || '').toLowerCase()
  const s3 = series3d(chart)
  const glType = k === 'bar3d' ? 'bar3D' : k === 'line3d' ? 'line3D' : 'scatter3D'
  return {
    backgroundColor: 'transparent',
    tooltip: {},
    xAxis3D: { type: 'value', name: chart?.x_label || 'X', nameTextStyle: { color: tc } },
    yAxis3D: { type: 'value', name: chart?.y_label || 'Y', nameTextStyle: { color: tc } },
    zAxis3D: { type: 'value', name: 'Z', nameTextStyle: { color: tc } },
    grid3D: {
      boxWidth: 100,
      boxDepth: 100,
      axisLabel: { textStyle: { color: tc, fontSize: 9 } },
      viewControl: { autoRotate: false, distance: 220 },
      light: { main: { intensity: 1.2 }, ambient: { intensity: 0.3 } },
    },
    series: s3.map((ss, i) => ({
      type: glType,
      name: ss.name,
      data: ss.data,
      symbolSize: 10,
      itemStyle: { color: ss.color || colorAt(i), opacity: glType === 'scatter3D' ? 0.85 : 1 },
      shading: glType === 'bar3D' ? 'lambert' : undefined,
      lineStyle: glType === 'line3D' ? { width: 3 } : undefined,
    })),
  } as unknown as EChartsOption
}
