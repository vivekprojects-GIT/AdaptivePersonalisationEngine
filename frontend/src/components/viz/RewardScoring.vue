<!--
  RewardScoring — APE's two-axis reward model from the deck (slide 11). Every user
  reaction is scored on TWO dimensions, content and format, and only the relevant
  one is learned from. Ends on the "protect rule": a content failure never
  penalizes a format that worked.
-->
<script setup lang="ts">
type Row = { signal: string; content: string; format: string; means: string }
const rows: Row[] = [
  { signal: 'Thumbs up',            content: '+2', format: '+2', means: 'Both worked' },
  { signal: 'Copy / save',          content: '+2', format: '+2', means: 'Worth keeping' },
  { signal: '“Make it shorter”',    content: '—',  format: '−2', means: 'Pure format failure' },
  { signal: '“That’s not right”', content: '−2', format: '—', means: 'Pure content failure' },
  { signal: 'Re-asks the question', content: '−1', format: '—',  means: 'Content didn’t land' },
  { signal: 'Thumbs down',          content: '−2', format: '−2', means: 'Both failed' },
  { signal: 'Regenerate',           content: '−2', format: '−2', means: 'Wants something else' },
  { signal: 'Asks a deeper question', content: '+1', format: '—', means: 'Content drove progress' },
]
const cls = (v: string) => (v.startsWith('+') ? 'pos' : v.startsWith('−') ? 'neg' : 'nul')
</script>

<template>
  <section class="max-w-7xl mx-auto px-5 lg:px-8 py-24">
    <div class="max-w-2xl mb-10" v-reveal>
      <span class="eyebrow">how reactions become learning</span>
      <h2 class="mt-3 text-4xl lg:text-5xl font-semibold tracking-[-0.03em]">Two axes, never confused.</h2>
      <p class="mt-4 text-base lg:text-lg text-muted-foreground">
        Not every bad reaction means the format was wrong. Each signal is scored on two
        dimensions — <span class="text-foreground">content</span> and
        <span class="text-foreground">format</span> — and APE only learns from the one that applies.
      </p>
    </div>

    <div class="ledger glass-panel" v-reveal="60">
      <div class="lrow lhead">
        <span>What the user does</span><span class="lc">Content</span><span class="lc">Format</span><span class="lm">What it means</span>
      </div>
      <div v-for="(r, i) in rows" :key="i" class="lrow">
        <span class="lsig">{{ r.signal }}</span>
        <span class="lc"><b :class="cls(r.content)">{{ r.content }}</b></span>
        <span class="lc"><b :class="cls(r.format)">{{ r.format }}</b></span>
        <span class="lm">{{ r.means }}</span>
      </div>
    </div>

    <div class="protect" v-reveal="120">
      <span class="protect-k">the protect rule</span>
      <p>A content failure <b>never</b> penalizes a format that worked. APE learns the right lesson —
        a wrong answer in a clean table doesn't blame the table.</p>
    </div>
  </section>
</template>

<style scoped>
.ledger { border: 1px solid var(--border); border-radius: 18px; overflow: hidden; }
.lrow {
  display: grid; grid-template-columns: 1.5fr 84px 84px 1.6fr; align-items: center;
  gap: 12px; padding: 13px 20px; border-top: 1px solid var(--border);
  transition: background 0.2s ease;
}
.lrow:first-child { border-top: 0; }
.lrow:not(.lhead):hover { background: color-mix(in oklab, var(--accent) 7%, transparent); }
.lhead {
  font: 600 10px/1.2 'JetBrains Mono', monospace; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--muted-foreground); background: color-mix(in oklab, #000 18%, var(--card));
}
.lhead .lm, .lhead span { color: var(--muted-foreground); }
.lc { text-align: center; }
.lsig { font-size: 14px; font-weight: 500; color: var(--foreground); }
.lm { font-size: 13px; color: var(--muted-foreground); }
.lc b {
  display: inline-grid; place-items: center; min-width: 34px; height: 26px; padding: 0 8px;
  font-family: 'JetBrains Mono', monospace; font-weight: 600; font-size: 13px; border-radius: 8px;
}
.lc b.pos { color: #34d399; background: rgba(52,211,153,0.12); border: 1px solid rgba(52,211,153,0.28); }
.lc b.neg { color: #fb7185; background: rgba(251, 113, 133, 0.10); border: 1px solid rgba(251, 113, 133, 0.26); }
.lc b.nul { color: var(--muted-foreground); opacity: 0.5; background: transparent; border: 0; }

.protect {
  margin-top: 20px; display: flex; flex-direction: column; gap: 8px;
  padding: 20px 22px; border-radius: 16px;
  background: color-mix(in oklab, var(--accent) 9%, var(--card));
  border: 1px solid color-mix(in oklab, var(--accent) 34%, transparent);
}
.protect-k {
  font: 600 10px/1 'JetBrains Mono', monospace; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--accent-strong);
}
.protect p { font-size: 15px; line-height: 1.5; color: var(--foreground); max-width: 62ch; }
.protect b { color: var(--accent-strong); }

@media (max-width: 720px) {
  .lrow { grid-template-columns: 1fr auto auto; }
  .lhead span:last-child, .lrow .lm { display: none; }
}
</style>
