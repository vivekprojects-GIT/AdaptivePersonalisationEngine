import { defineAsyncComponent, type Component } from 'vue'

// ── Per-plot custom components ──────────────────────────────────────────────
// Built-in chart KINDS (bar/pie/treemap/sankey/…) are drawn by the shared ECharts
// engine in `lib/echartsOption.ts` — kept together for DRY.
//
// This registry is the plug-in seam for plots that need their OWN code: a
// different charting library, D3, a WASM viz, or an external component vendored
// from another repo. Each such plot lives in its OWN self-contained folder under
// `chart/kinds/<name>/` (its .vue + css/js/adapter) and registers here.
//
// A custom plot component receives the SAME props as the built-in host:
//     defineProps<{ title?: string; chart: ChartSpec }>()
// and renders itself however it likes, reading data from `chart` (the registry
// JSON for that kind). ChartHost will mount it instead of the ECharts engine.
//
// Example — a Gantt plot vendored under ./gantt/:
//     gantt: () => import('./gantt/GanttPlot.vue'),
const CUSTOM_KINDS: Record<string, () => Promise<unknown>> = {
  // Real, self-contained plot components (own folder: <Name>Chart.vue + option.ts):
  pie: () => import('./pie/PieChart.vue'),
  donut: () => import('./pie/PieChart.vue'),
  funnel: () => import('./funnel/FunnelChart.vue'),
  gauge: () => import('./gauge/GaugeChart.vue'),
  radar: () => import('./radar/RadarChart.vue'),
  rose: () => import('./rose/RoseChart.vue'),
  heatmap: () => import('./heatmap/HeatmapChart.vue'),
  treemap: () => import('./treemap/TreemapChart.vue'),
  sunburst: () => import('./treemap/TreemapChart.vue'),
  waterfall: () => import('./waterfall/WaterfallChart.vue'),
  candlestick: () => import('./candlestick/CandlestickChart.vue'),
  boxplot: () => import('./boxplot/BoxplotChart.vue'),
  bubble: () => import('./bubble/BubbleChart.vue'),
  // network & flow
  sankey: () => import('./network/NetworkChart.vue'),
  graph: () => import('./network/NetworkChart.vue'),
  flow: () => import('./flow/FlowChart.vue'),
  flowchart: () => import('./flow/FlowChart.vue'),
  process: () => import('./flow/FlowChart.vue'),
  // circular / parallel
  polar: () => import('./polar/PolarChart.vue'),
  parallel: () => import('./parallel/ParallelChart.vue'),
  themeriver: () => import('./themeriver/ThemeriverChart.vue'),
  // hierarchy
  tree: () => import('./tree/TreeChart.vue'),
  mindmap: () => import('./tree/TreeChart.vue'),
  org: () => import('./tree/TreeChart.vue'),
  orgchart: () => import('./tree/TreeChart.vue'),
  // 3D (GL)
  scatter3d: () => import('./threed/ThreeDChart.vue'),
  bar3d: () => import('./threed/ThreeDChart.vue'),
  line3d: () => import('./threed/ThreeDChart.vue'),
  // cartesian family (line/bar/hbar/area/scatter/stacked/combo/histogram/timeseries)
  line: () => import('./cartesian/CartesianChart.vue'),
  bar: () => import('./cartesian/CartesianChart.vue'),
  hbar: () => import('./cartesian/CartesianChart.vue'),
  'horizontal-bar': () => import('./cartesian/CartesianChart.vue'),
  'horizontal_bar': () => import('./cartesian/CartesianChart.vue'),
  area: () => import('./cartesian/CartesianChart.vue'),
  scatter: () => import('./cartesian/CartesianChart.vue'),
  stacked: () => import('./cartesian/CartesianChart.vue'),
  'stacked-bar': () => import('./cartesian/CartesianChart.vue'),
  'stacked_bar': () => import('./cartesian/CartesianChart.vue'),
  combo: () => import('./cartesian/CartesianChart.vue'),
  histogram: () => import('./cartesian/CartesianChart.vue'),
  timeseries: () => import('./cartesian/CartesianChart.vue'),
  // gantt: () => import('./gantt/GanttPlot.vue'),   // external/library example
}

/** True if a kind is rendered by a custom per-plot component (not the ECharts engine). */
export function hasCustomKind(kind?: string): boolean {
  return !!CUSTOM_KINDS[String(kind || '').toLowerCase()]
}

/** Resolve the custom component for a kind, or null to use the built-in ECharts engine. */
export function resolveCustomKind(kind?: string): Component | null {
  const loader = CUSTOM_KINDS[String(kind || '').toLowerCase()]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return loader ? defineAsyncComponent(loader as any) : null
}
