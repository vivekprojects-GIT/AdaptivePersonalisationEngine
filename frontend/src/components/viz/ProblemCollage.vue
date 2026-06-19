<!--
  ProblemCollage — the "before APE" problem, made legible. Instead of a chaotic
  scatter, three clear mismatch rows: a person asks for one shape, most AI sends
  another. Each row reads left→right: who + what they wanted  →  what they got
  (wrong) + why it failed. The point lands at a glance.
-->
<script setup lang="ts">
type Row = {
  initial: string; name: string; wanted: string
  gotKind: 'wall' | 'oneline' | 'chart'; verdict: string
}
const rows: Row[] = [
  { initial: 'L', name: 'Leah',  wanted: 'a quick, skimmable answer',
    gotKind: 'wall',    verdict: '6 dense paragraphs — she bounced' },
  { initial: 'O', name: 'Omar',  wanted: 'the full side-by-side breakdown',
    gotKind: 'oneline', verdict: 'a one-liner — nothing to act on' },
  { initial: 'D', name: 'Dana',  wanted: 'it written out in prose',
    gotKind: 'chart',   verdict: 'a bar chart — the wrong shape entirely' },
]
</script>

<template>
  <section class="max-w-7xl mx-auto px-5 lg:px-8 py-20 lg:py-28">
    <div class="text-center max-w-2xl mx-auto" v-reveal>
      <h2 class="text-3xl sm:text-4xl lg:text-[52px] font-semibold tracking-[-0.035em] leading-[1.04]">
        One answer.<br class="sm:hidden" /> Every wrong shape.
      </h2>
      <p class="mt-4 text-base lg:text-lg text-muted-foreground">
        Most AI gives everyone the same reply in its one default format. The answer can be
        right — but the wrong shape makes it useless.
      </p>
    </div>

    <div class="rows">
      <div v-for="(r, i) in rows" :key="r.name" class="miscard" v-reveal :style="{ '--d': i * 80 + 'ms' }">
        <!-- what they asked for -->
        <div class="ask">
          <span class="av">{{ r.initial }}</span>
          <div class="ask-t">
            <b>{{ r.name }}</b>
            <span>wanted <em>{{ r.wanted }}</em></span>
          </div>
        </div>

        <!-- mismatch connector -->
        <div class="vs"><span class="x" aria-hidden="true">✕</span><span class="vs-l">got</span></div>

        <!-- what most AI actually sent (the wrong format) -->
        <div class="got">
          <span class="got-h">most AI sent</span>
          <div class="prev">
            <div v-if="r.gotKind === 'wall'" class="wall">
              <i></i><i></i><i style="width:82%"></i><i></i><i style="width:60%"></i>
            </div>
            <div v-else-if="r.gotKind === 'oneline'" class="oneline">“Roth usually wins.”</div>
            <div v-else class="chart"><i style="height:64%"></i><i style="height:42%"></i><i style="height:88%"></i><i style="height:30%"></i></div>
          </div>
          <div class="verdict"><span class="dot" aria-hidden="true"></span>{{ r.verdict }}</div>
        </div>
      </div>
    </div>

    <p class="punch" v-reveal>
      The answer was right. The <b>shape</b> was wrong — every time.
      <RouterLink to="/about" class="punch-link">See how APE fixes it <span aria-hidden="true">↓</span></RouterLink>
    </p>
  </section>
</template>

<style scoped>
.rows { margin: 48px auto 0; max-width: 760px; display: flex; flex-direction: column; gap: 16px; }

.miscard {
  display: grid;
  grid-template-columns: 1fr auto 1.5fr;
  align-items: center; gap: 18px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 18px 20px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04), 0 16px 34px -22px rgba(0, 0, 0, 0.5);
}

/* ASK side */
.ask { display: flex; align-items: center; gap: 11px; }
.av {
  width: 34px; height: 34px; flex: none; border-radius: 999px;
  background: var(--accent); color: var(--accent-foreground); display: grid; place-items: center;
  font: 600 13px/1 'Geist', sans-serif;
}
.ask-t { display: flex; flex-direction: column; line-height: 1.35; }
.ask-t b { font-size: 14px; }
.ask-t span { font-size: 13px; color: var(--muted-foreground); }
.ask-t em { font-style: normal; color: var(--foreground); font-weight: 500; }

/* connector */
.vs { display: flex; flex-direction: column; align-items: center; gap: 3px; }
.vs .x {
  width: 26px; height: 26px; display: grid; place-items: center; border-radius: 999px;
  background: color-mix(in oklab, var(--destructive) 16%, transparent); color: var(--destructive); font-size: 13px; font-weight: 700;
}
.vs-l { font: 600 8.5px/1 'JetBrains Mono', monospace; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted-foreground); }

/* GOT side */
.got { min-width: 0; }
.got-h { font: 600 9px/1 'JetBrains Mono', monospace; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted-foreground); }
.prev {
  margin-top: 7px; padding: 10px 12px; border-radius: 10px;
  background: color-mix(in oklab, #000 28%, var(--card)); border: 1px solid var(--border-medium);
}
.wall { display: flex; flex-direction: column; gap: 4px; }
.wall i { display: block; height: 5px; width: 100%; border-radius: 3px; background: color-mix(in oklab, var(--foreground) 28%, transparent); }
.oneline { font-size: 14px; font-weight: 500; color: var(--foreground); }
.chart { display: flex; align-items: flex-end; gap: 6px; height: 44px; }
.chart i { flex: 1; border-radius: 3px 3px 0 0; background: color-mix(in oklab, var(--foreground) 28%, transparent); }

.verdict { margin-top: 9px; display: flex; align-items: center; gap: 7px; font-size: 12.5px; font-weight: 500; color: var(--destructive); }
.verdict .dot { width: 6px; height: 6px; border-radius: 999px; background: var(--destructive); flex: none; }

.punch {
  margin: 40px auto 0; text-align: center; max-width: 640px;
  font-size: clamp(18px, 2.4vw, 24px); font-weight: 600; letter-spacing: -0.02em; line-height: 1.4;
}
.punch b { background: var(--accent); color: var(--accent-foreground); padding: 0 0.25em; border-radius: 0.16em; }
.punch-link {
  display: inline-flex; align-items: center; gap: 6px; margin-top: 12px;
  font-size: 14px; font-weight: 500; color: var(--accent-strong);
  transition: gap 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.punch-link { display: flex; justify-content: center; }
.punch-link:hover { gap: 11px; }

/* stack each row on small screens */
@media (max-width: 680px) {
  .miscard { grid-template-columns: 1fr; gap: 12px; text-align: left; }
  .vs { flex-direction: row; justify-content: flex-start; gap: 8px; }
}
</style>
