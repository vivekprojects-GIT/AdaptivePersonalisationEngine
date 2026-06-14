<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ block: { content?: string } }>()

// Escape first (safe), then apply a tiny markdown subset so the model's analysis can use
// "- " bullets and **bold**/`$ figures` highlighted in the accent color. No raw HTML allowed.
function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function inline(s: string): string {
  let t = esc(s)
  // **bold** and __bold__ → accent (blue) emphasis
  t = t.replace(/\*\*(.+?)\*\*/g, '<strong class="ws-accent">$1</strong>')
  t = t.replace(/__(.+?)__/g, '<strong class="ws-accent">$1</strong>')
  // `code` / inline figures
  t = t.replace(/`([^`]+?)`/g, '<code class="ws-code">$1</code>')
  return t
}

const html = computed(() => {
  const raw = String(props.block.content || '').replace(/\r\n/g, '\n').trim()
  if (!raw) return ''
  const lines = raw.split('\n')
  const out: string[] = []
  let list: 'ul' | 'ol' | null = null
  const closeList = () => {
    if (list) {
      out.push(`</${list}>`)
      list = null
    }
  }
  for (const line of lines) {
    const heading = line.match(/^\s*#{1,3}\s+(.*)$/)
    const ordered = line.match(/^\s*(\d+)[.)]\s+(.*)$/)
    const bullet = line.match(/^\s*[-*•]\s+(.*)$/)
    if (heading) {
      closeList()
      out.push(`<div class="ws-h">${inline(heading[1])}</div>`)
    } else if (ordered) {
      if (list !== 'ol') {
        closeList()
        out.push('<ol class="ws-ol">')
        list = 'ol'
      }
      out.push(`<li>${inline(ordered[2])}</li>`)
    } else if (bullet) {
      if (list !== 'ul') {
        closeList()
        out.push('<ul class="ws-bullets">')
        list = 'ul'
      }
      out.push(`<li>${inline(bullet[1])}</li>`)
    } else {
      closeList()
      if (line.trim()) out.push(`<p>${inline(line)}</p>`)
    }
  }
  closeList()
  return out.join('')
})
</script>

<template>
  <div
    class="ws-text leading-relaxed motion-safe:transition-opacity motion-safe:duration-300"
    v-html="html"
  />
</template>

<style scoped>
.ws-text :deep(p) {
  margin: 0 0 0.45em;
}
.ws-text :deep(p:last-child) {
  margin-bottom: 0;
}
.ws-text :deep(.ws-h) {
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: hsl(var(--muted-foreground));
  margin: 0.2em 0 0.5em;
}
.ws-text :deep(.ws-bullets) {
  margin: 0.25em 0;
  padding-left: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.4em;
}
.ws-text :deep(.ws-bullets li) {
  position: relative;
  padding-left: 1.1em;
}
.ws-text :deep(.ws-bullets li)::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.55em;
  width: 6px;
  height: 6px;
  border-radius: 9999px;
  background: hsl(var(--primary));
}
.ws-text :deep(.ws-ol) {
  margin: 0.25em 0;
  padding-left: 0;
  list-style: none;
  counter-reset: ws;
  display: flex;
  flex-direction: column;
  gap: 0.5em;
}
.ws-text :deep(.ws-ol li) {
  position: relative;
  padding-left: 1.9em;
  counter-increment: ws;
}
.ws-text :deep(.ws-ol li)::before {
  content: counter(ws);
  position: absolute;
  left: 0;
  top: 0.05em;
  width: 1.35em;
  height: 1.35em;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72em;
  font-weight: 700;
  border-radius: 9999px;
  color: hsl(var(--primary));
  background: hsl(var(--primary) / 0.12);
}
.ws-text :deep(.ws-accent) {
  color: hsl(var(--primary));
  font-weight: 600;
}
.ws-text :deep(.ws-code) {
  font-size: 0.88em;
  padding: 0.05em 0.35em;
  border-radius: 0.3rem;
  background: hsl(var(--primary) / 0.1);
  color: hsl(var(--primary));
}
</style>
