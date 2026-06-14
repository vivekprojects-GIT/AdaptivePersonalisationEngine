import type { EChartsOption } from 'echarts'
import { toNum, POSITIVE, NEGATIVE, type ChartSpec } from '@/lib/echartsOption'

/** Candlestick option — OHLC price action with zoom. */
export function candlestickOption(chart: ChartSpec, dark: boolean): EChartsOption {
  const tc = dark ? '#8d93aa' : '#5a5f72'
  const cats = chart?.x_categories || []
  const data = (chart?.candles || []).map((c) => (Array.isArray(c) ? c.slice(0, 4).map((v) => toNum(v) ?? 0) : []))
  return {
    backgroundColor: 'transparent',
    textStyle: { color: tc, fontSize: 11 },
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 16, top: 20, bottom: 56, containLabel: true },
    xAxis: { type: 'category', data: cats, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', scale: true, splitLine: { lineStyle: { opacity: 0.2 } } },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 8 }],
    series: [
      { type: 'candlestick', data, itemStyle: { color: POSITIVE, color0: NEGATIVE, borderColor: POSITIVE, borderColor0: NEGATIVE } },
    ],
  }
}
