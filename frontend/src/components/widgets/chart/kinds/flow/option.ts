import type { EChartsOption } from 'echarts'
import { colorAt, type ChartSpec } from '@/lib/echartsOption'

/** Flowchart option — directed graph laid out in LEFT→RIGHT layers, arrowed edges. */
export function flowOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  type FlowNode = { name: string; level?: number }
  const nodes: FlowNode[] = (chart?.nodes || []).map((n) =>
    typeof n === 'string' ? { name: n } : { name: n.name || '', level: n.level },
  )
  const links = (chart?.links || []).map((l) => ({
    source: String(l.source ?? ''),
    target: String(l.target ?? ''),
    label: l.label,
  }))
  const byName = new Map(nodes.map((n) => [n.name, n]))
  for (const l of links) {
    for (const e of [l.source, l.target]) {
      if (e && !byName.has(e)) {
        const nn = { name: e }
        nodes.push(nn)
        byName.set(e, nn)
      }
    }
  }

  const depth = new Map<string, number>()
  const incoming = new Map<string, number>()
  nodes.forEach((n) => incoming.set(n.name, 0))
  links.forEach((l) => incoming.set(l.target, (incoming.get(l.target) || 0) + 1))
  nodes.forEach((n) => depth.set(n.name, typeof n.level === 'number' ? n.level : 0))
  for (let pass = 0; pass < nodes.length; pass++) {
    let changed = false
    for (const l of links) {
      const d = Math.max(depth.get(l.target) || 0, (depth.get(l.source) || 0) + 1)
      if (d !== depth.get(l.target)) {
        depth.set(l.target, d)
        changed = true
      }
    }
    if (!changed) break
  }

  const cols = new Map<number, string[]>()
  nodes.forEach((n) => {
    const d = depth.get(n.name) || 0
    if (!cols.has(d)) cols.set(d, [])
    cols.get(d)!.push(n.name)
  })
  const maxDepth = Math.max(0, ...Array.from(cols.keys()))
  const placed = nodes.map((n, i) => {
    const d = depth.get(n.name) || 0
    const col = cols.get(d)!
    const row = col.indexOf(n.name)
    const x = maxDepth > 0 ? (d / maxDepth) * 100 : 50
    const y = col.length > 1 ? (row / (col.length - 1)) * 100 : 50
    return {
      name: n.name,
      x,
      y,
      value: 1,
      symbol: 'roundRect',
      symbolSize: [Math.min(120, Math.max(54, n.name.length * 7)), 34] as [number, number],
      itemStyle: { color: colorAt(i, nodes.length), borderColor: 'rgba(255,255,255,0.65)', borderWidth: 1 },
      label: { show: true, color: '#fff', fontSize: 11, fontWeight: 600 as const, overflow: 'truncate' as const, width: 110 },
    }
  })

  return {
    backgroundColor: 'transparent',
    textStyle: { color: tc, fontSize: 11 },
    tooltip: { trigger: 'item' },
    series: [
      {
        type: 'graph',
        layout: 'none',
        roam: true,
        data: placed,
        links: links.map((l) => ({
          source: l.source,
          target: l.target,
          label: l.label ? { show: true, formatter: l.label, fontSize: 9, color: tc } : undefined,
          lineStyle: { color: dark ? 'rgba(255,255,255,0.45)' : 'rgba(71,85,105,0.6)', width: 1.5, curveness: 0.05 },
        })),
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: [0, 9],
        emphasis: { focus: 'adjacency' },
        label: { position: 'inside' },
      },
    ],
  } as EChartsOption
}
