import { onMounted, onUnmounted, watch, nextTick, type Ref } from 'vue'
import * as echarts from 'echarts'
import { applyTheme } from '@/lib/echartsOption'

/**
 * Shared ECharts plumbing for per-plot components — init, theme, resize, dispose,
 * PNG export. Each plot component supplies its OWN raw `option` via getOption();
 * this composable handles the lifecycle so the per-plot files stay focused on
 * their chart. (3D plots additionally `import 'echarts-gl'` in their own file.)
 */
export function useEChart(
  rootEl: Ref<HTMLDivElement | null>,
  getOption: () => echarts.EChartsOption,
  watchSrc?: () => unknown,
) {
  let inst: echarts.ECharts | null = null
  let ro: ResizeObserver | null = null
  let raf = 0
  let first = true

  const isDark = () =>
    typeof matchMedia !== 'undefined' && matchMedia('(prefers-color-scheme: dark)').matches

  function resize() {
    if (raf) return
    raf = requestAnimationFrame(() => {
      raf = 0
      inst?.resize()
    })
  }

  function render() {
    nextTick(() => {
      if (!rootEl.value) return
      if (!inst) {
        inst = echarts.init(rootEl.value, undefined, { renderer: 'canvas' })
        if (typeof ResizeObserver !== 'undefined') {
          ro = new ResizeObserver(() => resize())
          ro.observe(rootEl.value)
        }
      }
      // First paint: notMerge (clean). Updates (streaming re-parses, prop changes):
      // merge → ECharts diffs the option, so identical/incremental data does NOT
      // replay the entrance animation → smooth, no flicker.
      inst.setOption(applyTheme(getOption(), isDark()), first)
      first = false
    })
  }

  function toPng(title = 'chart') {
    if (!inst) return
    const url = inst.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: isDark() ? '#13151c' : '#ffffff' })
    const name = String(title).replace(/[^a-zA-Z0-9_-]+/g, '-').replace(/^-|-$/g, '').slice(0, 60) || 'chart'
    const a = document.createElement('a')
    a.href = url
    a.download = `${name}.png`
    document.body.appendChild(a)
    a.click()
    a.remove()
  }

  onMounted(() => {
    render()
    window.addEventListener('resize', resize)
  })
  onUnmounted(() => {
    window.removeEventListener('resize', resize)
    if (raf) cancelAnimationFrame(raf)
    ro?.disconnect()
    ro = null
    inst?.dispose()
    inst = null
  })
  if (watchSrc) watch(watchSrc, render, { deep: true })

  return { render, toPng }
}
