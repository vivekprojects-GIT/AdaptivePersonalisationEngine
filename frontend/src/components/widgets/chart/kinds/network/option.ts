import type { EChartsOption } from 'echarts'
import { toNum, colorAt, type ChartSpec } from '@/lib/echartsOption'

/** Sankey / force-graph option — flows & networks (nodes + links). */
export function networkOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const isGraph = String(chart?.kind || '').toLowerCase() === 'graph'
  const nodes = (chart?.nodes || []).map((n) => ({ name: typeof n === 'string' ? n : n.name || '' }))
  const links = (chart?.links || []).map((l) => ({ source: l.source, target: l.target, value: toNum(l.value) ?? 1 }))
  const named = new Set(nodes.map((n) => n.name))
  for (const l of links) {
    for (const e of [l.source, l.target]) {
      const s = String(e)
      if (e != null && !named.has(s)) {
        nodes.push({ name: s })
        named.add(s)
      }
    }
  }
  const coloredNodes = nodes.map((nd, i) => ({ ...nd, itemStyle: { color: colorAt(i, nodes.length) } }))
  return {
    backgroundColor: 'transparent',
    textStyle: { color: tc, fontSize: 11 },
    tooltip: { trigger: 'item' },
    series: [
      isGraph
        ? { type: 'graph', layout: 'force', roam: true, data: coloredNodes, links, label: { show: true, fontSize: 10 }, force: { repulsion: 140 } }
        : { type: 'sankey', data: coloredNodes, links, label: { fontSize: 10, color: tc }, emphasis: { focus: 'adjacency' }, lineStyle: { color: 'gradient', opacity: 0.5 } },
    ],
  } as EChartsOption
}
