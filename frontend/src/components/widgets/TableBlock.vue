<script setup lang="ts">
import { computed } from 'vue'

type Col = string | { label?: string; name?: string; title?: string; key?: string; field?: string }

const props = defineProps<{
  block: { title?: string; columns?: Col[]; rows?: unknown[] }
}>()

// A column may arrive as a plain string or as an object like {label,key}.
// Always show a clean header string, never raw JSON.
function colLabel(c: Col): string {
  if (c == null) return ''
  if (typeof c === 'string') return c
  return String(c.label ?? c.name ?? c.title ?? c.key ?? c.field ?? '')
}

// The key used to read object-shaped rows for this column (falls back to label).
function colKey(c: Col): string {
  if (c == null) return ''
  if (typeof c === 'string') return c
  return String(c.key ?? c.field ?? c.label ?? c.name ?? '')
}

const cols = computed<Col[]>(() => (Array.isArray(props.block?.columns) ? props.block.columns : []))

// Normalize each row to an array of cells aligned to the columns, whether the
// row came in as a positional array or as an object keyed by column key.
const rows = computed<unknown[][]>(() => {
  const raw = Array.isArray(props.block?.rows) ? props.block.rows : []
  return raw.map((row) => {
    if (Array.isArray(row)) return row
    if (row && typeof row === 'object') {
      const obj = row as Record<string, unknown>
      if (cols.value.length) return cols.value.map((c) => obj[colKey(c)] ?? '')
      return Object.values(obj)
    }
    return [row]
  })
})

function cellText(cell: unknown): string {
  if (cell == null) return ''
  if (typeof cell === 'object') return JSON.stringify(cell)
  return String(cell)
}
</script>

<template>
  <div class="rounded-xl border bg-card overflow-hidden transition-shadow duration-300 hover:shadow-md">
    <div v-if="block.title" class="px-3 py-2 border-b text-xs font-medium">{{ block.title }}</div>
    <div class="overflow-x-auto">
      <table class="w-full text-xs">
        <thead v-if="cols.length">
          <tr>
            <th
              v-for="(c, ci) in cols"
              :key="ci"
              class="text-left px-3 py-2 border-b bg-muted/40 font-medium"
            >
              {{ colLabel(c) }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, ri) in rows" :key="ri">
            <td v-for="(cell, ci) in row" :key="ci" class="px-3 py-1.5 border-b border-border/60">
              {{ cellText(cell) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
