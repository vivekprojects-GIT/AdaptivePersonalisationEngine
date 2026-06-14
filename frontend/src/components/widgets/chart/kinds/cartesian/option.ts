import type { EChartsOption } from 'echarts'
import { cartesianSeries, cartesianCategories, makeFmtVal, areaGradient, withAlpha, type ChartSpec } from '@/lib/echartsOption'

/** Cartesian family — line / bar / hbar / area / scatter / stacked / combo / histogram / timeseries. */
export function cartesianOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const k = String(chart?.kind || 'line').toLowerCase()
  const fmtVal = makeFmtVal(chart)

  const series = cartesianSeries(chart)
  const isHBar = k === 'hbar' || k === 'horizontal-bar' || k === 'horizontal_bar'
  const isStacked = k === 'stacked' || k === 'stacked-bar' || k === 'stacked_bar'
  const isCombo = k === 'combo'
  const isBar = k === 'bar' || k === 'histogram' || isStacked || isHBar
  const isScatter = k === 'scatter' || k === 'bubble'
  const isArea = k === 'area' || k === 'timeseries'

  const cats = cartesianCategories(chart)
  const useCat = Array.isArray(cats) && cats.length > 0

  const catCount = cats?.length ?? series[0]?.points.length ?? 0
  const fewBars = catCount > 0 && catCount <= 12 && series.length <= 4
  const fewPts = catCount > 0 && catCount <= 8 && series.length <= 2

  const eSeries = series.map((s, i) => {
    const seriesType = (
      isCombo ? (s.kind === 'line' ? 'line' : s.kind === 'bar' ? 'bar' : i === 0 ? 'bar' : 'line')
      : isBar ? 'bar'
      : isScatter ? 'scatter'
      : 'line'
    ) as 'bar' | 'scatter' | 'line'
    const asLine = seriesType === 'line'
    const isBarSeries = seriesType === 'bar'
    return {
      name: s.name,
      type: seriesType,
      data: useCat ? s.points.map((p) => p[1]) : s.points,
      stack: isStacked ? 'total' : undefined,
      smooth: asLine ? 0.35 : undefined,
      showSymbol: seriesType === 'scatter' || (asLine && fewPts),
      symbolSize: seriesType === 'scatter' ? 10 : 7,
      label: isBarSeries
        ? {
            show: isStacked ? catCount <= 8 : fewBars,
            position: (isStacked ? 'inside' : isHBar ? 'right' : 'top') as 'inside' | 'right' | 'top',
            fontSize: 10,
            fontWeight: 600 as const,
            color: isStacked ? '#fff' : tc,
            formatter: (p: any) => fmtVal(p.value),
          }
        : asLine
          ? { show: fewPts, position: 'top' as const, fontSize: 10, color: tc, formatter: (p: any) => fmtVal(p.value) }
          : undefined,
      itemStyle: {
        color: s.color,
        borderRadius: isBarSeries ? (isHBar ? [0, 4, 4, 0] : [4, 4, 0, 0]) : undefined,
      },
      areaStyle: isArea && asLine ? { color: areaGradient(s.color) } : undefined,
      lineStyle: asLine ? { width: 2.5 } : undefined,
      emphasis: { focus: 'series' as const, scale: seriesType === 'scatter', itemStyle: { shadowBlur: 10, shadowColor: withAlpha(s.color, 0.5) } },
      animationDuration: 900,
      animationEasing: 'cubicOut' as const,
    }
  })

  const legendNames = series.map((s) => s.name)
  const valueAxis = {
    type: 'value' as const,
    name: (isHBar ? chart?.x_label : chart?.y_label) || '',
    nameLocation: 'middle' as const,
    nameGap: 36,
    splitLine: { show: true, lineStyle: { opacity: 0.2 } },
  }
  const catAxis = useCat
    ? {
        type: 'category' as const,
        data: cats,
        name: (isHBar ? chart?.y_label : chart?.x_label) || '',
        nameLocation: (isHBar ? 'end' : 'middle') as 'end' | 'middle',
        nameGap: isHBar ? 12 : (cats as string[]).length > 6 ? 42 : 28,
        nameTextStyle: isHBar ? { align: 'right' as const, color: tc } : { color: tc },
        axisLabel: { fontSize: 10, rotate: !isHBar && (cats as string[]).length > 6 ? 30 : 0 },
      }
    : {
        type: 'value' as const,
        name: (isHBar ? chart?.y_label : chart?.x_label) || '',
        nameLocation: 'middle' as const,
        nameGap: 28,
        splitLine: { show: true, lineStyle: { opacity: 0.2 } },
      }

  const wantsZoom =
    !isHBar &&
    !isScatter &&
    (k === 'timeseries' || ((k === 'line' || k === 'area') && useCat && (cats as string[]).length > 10))

  return {
    animation: true,
    animationDuration: 1100,
    backgroundColor: 'transparent',
    textStyle: { color: tc, fontSize: 11 },
    grid: { left: 48, right: 24, top: 36, bottom: wantsZoom ? 64 : 40, containLabel: true },
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' }, valueFormatter: (v: any) => fmtVal(v) },
    legend: legendNames.length > 1 ? { data: legendNames, bottom: 0, textStyle: { color: tc, fontSize: 10 } } : undefined,
    dataZoom: wantsZoom ? [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 8 }] : undefined,
    xAxis: isHBar ? valueAxis : catAxis,
    yAxis: isHBar ? catAxis : valueAxis,
    series: eSeries,
  } as EChartsOption
}
