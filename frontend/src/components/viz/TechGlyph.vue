<script setup lang="ts">
/** TechGlyph — clean monochrome line glyphs for the tech-stack strip.
 *  Stroke uses currentColor so each adapts to its card's accent. */
defineProps<{ name: string }>()
</script>

<template>
  <!-- Python -->
  <svg v-if="name === 'python'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="h-full w-full" aria-hidden="true">
    <path d="M9 7h4a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2H8a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h3" />
    <path d="M15 17h-4a2 2 0 0 1-2-2V13a2 2 0 0 1 2-2h5a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-3" />
    <circle cx="9.5" cy="6.5" r=".6" fill="currentColor" stroke="none" />
    <circle cx="14.5" cy="17.5" r=".6" fill="currentColor" stroke="none" />
  </svg>

  <!-- FastAPI -->
  <svg v-else-if="name === 'fastapi'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="h-full w-full" aria-hidden="true">
    <circle cx="12" cy="12" r="8.5" />
    <path d="M12.5 6.5 8.5 12.8H12l-.6 4.7 4-6.3H12z" fill="currentColor" stroke="none" />
  </svg>

  <!-- Vue -->
  <svg v-else-if="name === 'vue'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" class="h-full w-full" aria-hidden="true">
    <path d="M4 6h3.5L12 13l4.5-7H20l-8 13z" />
  </svg>

  <!-- AWS Lambda -->
  <svg v-else-if="name === 'lambda'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="h-full w-full" aria-hidden="true">
    <path d="M6 18 11 6h2l5 12" />
    <path d="M9.5 11.5 6 18" />
  </svg>

  <!-- DynamoDB (database) -->
  <svg v-else-if="name === 'dynamodb'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="h-full w-full" aria-hidden="true">
    <ellipse cx="12" cy="6.5" rx="6" ry="2.5" />
    <path d="M6 6.5v11c0 1.4 2.7 2.5 6 2.5s6-1.1 6-2.5v-11" />
    <path d="M6 12c0 1.4 2.7 2.5 6 2.5s6-1.1 6-2.5" />
  </svg>

  <!-- MongoDB (leaf) -->
  <svg v-else-if="name === 'mongo'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="h-full w-full" aria-hidden="true">
    <path d="M12 3c3 4 4 7 4 10a4 4 0 0 1-8 0c0-3 1-6 4-10z" />
    <path d="M12 7v14" />
  </svg>

  <!-- ECharts (bars) -->
  <svg v-else-if="name === 'echarts'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="h-full w-full" aria-hidden="true">
    <path d="M4 20h16" />
    <rect x="6" y="11" width="3" height="6" rx="1" />
    <rect x="11" y="7" width="3" height="10" rx="1" />
    <rect x="16" y="13" width="3" height="4" rx="1" />
  </svg>

  <!-- Statistics (UCB / bell curve) -->
  <svg v-else-if="name === 'stats'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="h-full w-full" aria-hidden="true">
    <path d="M3 18h18" />
    <path d="M4 18c3 0 3.5-9 8-9s5 9 8 9" />
  </svg>

  <!-- Figma -->
  <svg v-else-if="name === 'figma'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="h-full w-full" aria-hidden="true">
    <path d="M12 4H9.5a2.5 2.5 0 0 0 0 5H12z" />
    <path d="M12 4h2.5a2.5 2.5 0 0 1 0 5H12z" />
    <path d="M12 9H9.5a2.5 2.5 0 0 0 0 5H12z" />
    <circle cx="14.5" cy="11.5" r="2.5" />
    <path d="M12 14H9.5a2.5 2.5 0 1 0 2.5 2.5z" />
  </svg>

  <!-- Claude / LLM (sparkle) -->
  <svg v-else-if="name === 'claude'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="h-full w-full" aria-hidden="true">
    <path d="M12 4c.6 3.6 1.8 4.8 5.4 5.4-3.6.6-4.8 1.8-5.4 5.4-.6-3.6-1.8-4.8-5.4-5.4C10.2 8.8 11.4 7.6 12 4z" />
    <path d="M18 15c.3 1.5.8 2 2.3 2.3-1.5.3-2 .8-2.3 2.3-.3-1.5-.8-2-2.3-2.3 1.5-.3 2-.8 2.3-2.3z" />
  </svg>

  <!-- fallback dot -->
  <svg v-else viewBox="0 0 24 24" class="h-full w-full" aria-hidden="true"><circle cx="12" cy="12" r="3" fill="currentColor" /></svg>
</template>
