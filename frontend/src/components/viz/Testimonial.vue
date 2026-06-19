<!--
  Testimonial — Ramp-style full-bleed quote block (ref: their "Before Ramp…"
  section). Big quote over a dark cool gradient. PLACEHOLDER copy, badged
  "SAMPLE" — replace with a real, attributed design-partner quote.
-->
<script setup lang="ts"></script>

<template>
  <section class="testi" v-reveal>
    <div class="inner">
      <span class="badge">sample testimonial</span>
      <blockquote>
        “Before APE, every user got the same wall of text. Now the skimmer gets a
        one-liner and the analyst gets a table — and we never touched a prompt.”
      </blockquote>
      <div class="attr">
        <span class="dot" aria-hidden="true"></span>
        <div><b>Name, Role</b><span>Company · placeholder quote</span></div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.testi {
  position: relative; overflow: hidden;
  margin: 24px auto; max-width: 80rem;
  border-radius: 28px;
  background:
    radial-gradient(120% 140% at 12% 0%, color-mix(in oklab, var(--accent) 18%, #131316) 0%, #131316 48%, #0a0a0c 100%);
  color: #fff;
}
.inner { padding: 64px 40px 56px; max-width: 900px; }
@media (min-width: 1024px) { .inner { padding: 100px 80px 90px; } }

.badge {
  display: inline-block; margin-bottom: 28px;
  font: 600 10px/1 'JetBrains Mono', monospace; letter-spacing: 0.14em; text-transform: uppercase;
  color: rgba(255, 255, 255, 0.55);
  padding: 6px 10px; border: 1px solid rgba(255, 255, 255, 0.18); border-radius: 999px;
}
blockquote {
  font-family: 'Geist', sans-serif; font-weight: 600;
  font-size: clamp(24px, 4vw, 44px); line-height: 1.18; letter-spacing: -0.025em;
  max-width: 18ch;
}
@media (min-width: 768px) { blockquote { max-width: 24ch; } }
.attr { display: flex; align-items: center; gap: 12px; margin-top: 36px; }
.attr .dot { width: 40px; height: 40px; border-radius: 999px; background: linear-gradient(135deg, var(--accent-strong), var(--accent)); flex: none; }
.attr b { display: block; font-size: 15px; }
.attr span { font-size: 13px; color: rgba(255, 255, 255, 0.6); }
</style>
