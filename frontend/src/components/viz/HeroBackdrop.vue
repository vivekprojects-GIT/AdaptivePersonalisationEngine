<!--
  HeroBackdrop — the landing hero backdrop. Default is the live BrainCloneHero
  (a 3D human mind mirror-cloned into an AI brain, DECIDE intents streaming
  across). If a looping hero video is ever supplied it takes precedence; both
  respect reduced-motion (the canvas renders a calm static frame).

  To switch the hero to video instead: drop the clip at frontend/public/hero/loop.mp4
  and set HERO_VIDEO below to '/hero/loop.mp4'. That's the only change needed.
-->
<template>
  <video
    v-if="HERO_VIDEO && !reduce"
    class="hero-video"
    :poster="HERO_POSTER || undefined"
    autoplay muted loop playsinline preload="auto"
    aria-hidden="true"
  >
    <source :src="HERO_VIDEO" type="video/mp4" />
  </video>
  <BrainCloneHero v-else />
</template>

<script setup lang="ts">
import BrainCloneHero from './BrainCloneHero.vue'

const HERO_VIDEO = ''   // e.g. '/hero/loop.mp4' once a clip is generated
const HERO_POSTER = ''  // e.g. '/hero/loop.jpg' first-frame still

const reduce = typeof window !== 'undefined'
  && window.matchMedia('(prefers-reduced-motion: reduce)').matches
</script>

<style scoped>
.hero-video {
  position: absolute; inset: 0; width: 100%; height: 100%;
  object-fit: cover; z-index: 0; pointer-events: none;
}
</style>
