// Shared hero state: the SAME question, asked by different people, answered in
// each one's preferred format. MorphingAnswer (the central card) and HeroCollage
// (the floating engine cards) both read this so they stay in lockstep as the
// demo cycles — the whole hero "changes according to the question + response".

export type Persona = {
  name: string
  initial: string
  fmt: 'table' | 'chart' | 'bullets' | 'oneline' | 'prose'
  label: string   // the format chip text
  note: string    // why this person likes that shape
  intent: string  // classified intent for this turn
  reward: number  // reward APE banked after applying this format
}

export const personas: Persona[] = [
  { name: 'Priya',  initial: 'P', fmt: 'table',   label: 'comparison table', note: 'reads the full breakdown', intent: 'compare', reward: 0.42 },
  { name: 'Marcus', initial: 'M', fmt: 'oneline', label: 'one-liner',        note: 'just wants the verdict',  intent: 'decide',  reward: 0.31 },
  { name: 'Dana',   initial: 'D', fmt: 'bullets', label: 'bullet summary',   note: 'skims the key points',    intent: 'compare', reward: 0.38 },
  { name: 'Sam',    initial: 'S', fmt: 'chart',   label: 'bar chart',        note: 'thinks in visuals',       intent: 'compare', reward: 0.45 },
  { name: 'Alex',   initial: 'A', fmt: 'prose',   label: 'short paragraph',  note: 'likes the full story',    intent: 'explain', reward: 0.29 },
]

// The UCB arms shown in the "selecting format" card, in catalog order.
export const ARMS: { key: Persona['fmt']; label: string }[] = [
  { key: 'table',   label: 'table' },
  { key: 'chart',   label: 'chart' },
  { key: 'bullets', label: 'bullets' },
  { key: 'oneline', label: 'one-line' },
  { key: 'prose',   label: 'prose' },
]

// The three intents the classifier card lights up between.
export const INTENTS = ['compare', 'explain', 'decide']

export const CYCLE_MS = 2900
