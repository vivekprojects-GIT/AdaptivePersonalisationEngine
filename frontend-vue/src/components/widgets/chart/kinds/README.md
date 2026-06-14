# chart/kinds — per-plot components

Built-in chart kinds (bar, line, pie, treemap, sankey, flow, …) are drawn by the
**shared ECharts engine** in `src/lib/echartsOption.ts`. They stay together for DRY —
each is a small `option`-builder branch, not a separate file.

Use **this folder** for a plot that needs its **own code or library** — a different
charting lib, D3, a WASM module, or an external component from another repo. Each
such plot is a **self-contained folder** here.

## How to add a per-plot component

1. **Vendor / install** the component (npm, `degit <repo>/<subpath>`, or copy files)
   into its own folder, e.g. `chart/kinds/gantt/`:

   ```
   chart/kinds/gantt/
     GanttPlot.vue      # the component (may use any library)
     gantt.css          # its own styles
     adapter.ts         # optional: maps our `chart` JSON -> the lib's props
   ```

2. **Register the contract** in `src/widget-registry.json` (add the new kind to the
   `chart` block's `kinds` list + a `spec` line) so the LLM emits the right JSON and
   the backend allows it.

3. **Register the component** in `chart/kinds/registry.ts`:

   ```ts
   const CUSTOM_KINDS = {
     gantt: () => import('./gantt/GanttPlot.vue'),
   }
   ```

4. The component receives the same props as the built-in host:

   ```ts
   defineProps<{ title?: string; chart: ChartSpec }>()
   ```

   Read your data from `chart` and render however you like. `ChartHost` mounts it
   instead of the ECharts engine when the kind matches.

## Notes
- Lazy `() => import()` keeps each plot code-split (loads only when used).
- The component runs **in-app** (full access) — only vendor code you trust.
- For other-framework components: wrap as a **web component**, mount adapter, or
  (fully isolated) render in a sandboxed iframe.
