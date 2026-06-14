import type { EChartsOption } from 'echarts'
import { treeRoot, colorAt, type ChartSpec } from '@/lib/echartsOption'

/** Tree / mindmap / org — a single hierarchical root. */
export function treeOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const k = String(chart?.kind || '').toLowerCase()
  const root = treeRoot(chart) || { name: '·' }
  const radial = k === 'mindmap'
  const topDown = k === 'org' || k === 'orgchart'
  return {
    backgroundColor: 'transparent',
    textStyle: { color: tc, fontSize: 11 },
    tooltip: { trigger: 'item', triggerOn: 'mousemove' },
    series: [
      {
        type: 'tree',
        data: [root],
        layout: radial ? 'radial' : 'orthogonal',
        orient: topDown ? 'TB' : 'LR',
        roam: true,
        symbol: 'circle',
        symbolSize: 9,
        itemStyle: { color: colorAt(0) },
        lineStyle: { color: dark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.2)', width: 1.2, curveness: radial ? 0.3 : 0.5 },
        label: {
          position: radial ? 'right' : topDown ? 'top' : 'left',
          verticalAlign: 'middle',
          align: radial ? 'left' : topDown ? 'center' : 'right',
          fontSize: 11,
          color: tc,
        },
        leaves: { label: { position: topDown ? 'bottom' : 'right', align: topDown ? 'center' : 'left' } },
        expandAndCollapse: true,
        initialTreeDepth: -1,
        animationDuration: 600,
      },
    ],
  } as EChartsOption
}
