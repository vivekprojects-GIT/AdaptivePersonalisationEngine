<!--
  FormatWall — Ramp-style cell grid (ref: their customer logo wall), reframed
  honestly for APE: the catalog of shapes APE picks between, as hairline-separated
  cells, with one featured dark stat card on the right (Ramp's "7 mo" tile).
  No fabricated customer logos — these are APE's own output formats.
  Layout: a clean cell grid (2-col → 4-col) beside a full-height feature card;
  cell count fills complete rows so no empty tracks at any width.
-->
<script setup lang="ts">
const formats = [
  'Comparison table', 'Bar chart', 'Bullet summary', 'One-liner',
  'Short prose', 'Checklist', 'Timeline', 'Heatmap',
]
</script>

<template>
  <section class="max-w-7xl mx-auto px-5 lg:px-8 py-16 lg:py-24">
    <div class="max-w-2xl" v-reveal>
      <h2 class="text-2xl sm:text-3xl lg:text-[40px] font-semibold leading-[1.1]">
        One answer, every shape.
        <span class="text-muted-foreground">APE picks between 18 formats — and learns which one each person keeps.</span>
      </h2>
      <RouterLink to="/about" class="report-link">
        See how it decides <span aria-hidden="true">→</span>
      </RouterLink>
    </div>

    <div class="wall" v-reveal>
      <div class="cells">
        <div v-for="(f, i) in formats" :key="f" class="cell">
          <span class="cell-label">{{ f }}</span>
          <span v-if="i === 1 || i === 6" class="cell-arrow" aria-hidden="true">→</span>
        </div>
      </div>

      <!-- featured dark stat card (ref: Ramp's "7 mo" Poshmark tile) -->
      <div class="feature">
        <span class="feat-eyebrow">live engine</span>
        <div class="feat-stat"><span class="num">3</span><span class="unit">ms</span></div>
        <div class="feat-sub">median format decision, per turn</div>
        <span class="feat-arrow" aria-hidden="true">→</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.report-link {
  display: inline-flex; align-items: center; gap: 6px; margin-top: 16px;
  font-size: 14px; font-weight: 500; color: var(--foreground);
  transition: gap 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.report-link:hover { gap: 11px; }

.wall {
  margin-top: 40px;
  display: grid; grid-template-columns: 1fr;
  gap: 1px; background: var(--border);
  border: 1px solid var(--border); border-radius: 18px; overflow: hidden;
}
@media (min-width: 1024px) { .wall { grid-template-columns: minmax(0, 1fr) 320px; } }

.cells {
  display: grid; grid-template-columns: repeat(2, 1fr);
  gap: 1px; background: var(--border);
}
@media (min-width: 640px) { .cells { grid-template-columns: repeat(4, 1fr); } }

.cell {
  position: relative; background: var(--card); min-height: 118px;
  display: grid; place-items: center; padding: 18px;
  transition: background 0.25s ease;
}
.cell:hover { background: color-mix(in oklab, var(--accent) 14%, var(--card)); }
.cell-label {
  font-size: 13px; font-weight: 500; letter-spacing: -0.01em;
  color: var(--muted-foreground); text-align: center; transition: color 0.25s ease;
}
.cell:hover .cell-label { color: var(--foreground); }
.cell-arrow {
  position: absolute; top: 12px; right: 12px;
  width: 22px; height: 22px; display: grid; place-items: center;
  border-radius: 999px; background: var(--secondary); color: var(--foreground);
  font-size: 12px; opacity: 0; transform: translateY(-3px);
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.cell:hover .cell-arrow { opacity: 1; transform: translateY(0); }

/* featured dark tile — full height beside the grid on desktop */
.feature {
  position: relative; color: #fff; padding: 22px;
  display: flex; flex-direction: column; justify-content: flex-end; min-height: 160px;
  background: radial-gradient(130% 90% at 80% 8%, #2a2928 0%, #15140f 55%, #0c0a08 100%);
}
.feat-eyebrow {
  position: absolute; top: 18px; left: 22px;
  font: 600 10px/1 'JetBrains Mono', monospace; letter-spacing: 0.1em;
  text-transform: uppercase; color: rgba(255, 255, 255, 0.6);
}
.feat-stat { display: flex; align-items: baseline; gap: 4px; }
.feat-stat .num {
  font-family: 'JetBrains Mono', monospace; font-weight: 600;
  font-size: 58px; line-height: 0.9; letter-spacing: -0.04em;
}
.feat-stat .unit { font-size: 22px; font-weight: 500; color: rgba(255, 255, 255, 0.7); }
.feat-sub { margin-top: 8px; font-size: 13px; color: rgba(255, 255, 255, 0.66); max-width: 220px; }
.feat-arrow {
  position: absolute; top: 16px; right: 18px;
  width: 26px; height: 26px; display: grid; place-items: center;
  border-radius: 999px; background: rgba(255, 255, 255, 0.12); color: #fff; font-size: 13px;
}
</style>
