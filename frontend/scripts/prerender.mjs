// Post-build prerender (runs after `vite build`).
//
// A Vite SPA ships an empty <div id="app"></div>; the content only exists after
// JS runs. Googlebot renders JS, but its first pass — and crawlers that DON'T
// run JS at all (GPTBot, PerplexityBot, Bing, social unfurlers) — see nothing.
// This injects a static, SEO-critical snapshot of the landing page into the
// served HTML so every crawler gets real, topical content. Vue replaces this
// block the instant it mounts, so interactive users are unaffected.
//
// Keep this copy in sync with the hero in src/pages/Home.vue.

import { readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const indexPath = resolve(here, '..', 'dist', 'index.html')

const snapshot = `<div id="app"><main style="max-width:880px;margin:0 auto;padding:72px 24px;font-family:Inter,system-ui,sans-serif;color:#1c1c17">
<p style="font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#57574e;font-weight:600;margin:0">The response-format layer</p>
<h1 style="font-size:44px;line-height:1.12;font-weight:700;margin:14px 0 0">Answers that take your shape</h1>
<p style="font-size:18px;line-height:1.6;color:#4b4b42;max-width:640px;margin:18px 0 0">APE learns the response format each user prefers — table, chart, prose, steps — and serves it through one API. The personalisation layer that sits on top of your memory, RAG, or agent stack: the one thing they don't do.</p>
<p style="margin:28px 0 0"><a href="/login?mode=register" style="color:#1c1c17;font-weight:600">Get started, it's free</a> &middot; <a href="/app/about" style="color:#4b4b42">How it works</a></p>
<ul style="margin:34px 0 0;padding-left:18px;color:#4b4b42;line-height:1.9;max-width:640px">
<li>Picks the answer format per user and per question type, live on every turn.</li>
<li>One HTTP call. Drops into any LLM, RAG, or agent stack with zero added latency.</li>
<li>Learns from a thumbs-up or a "make it shorter"; every pick is auditable.</li>
<li>Governed visuals: charts and tables render from a closed component registry.</li>
</ul>
<nav style="margin:34px 0 0;font-size:14px;color:#57574e"><a href="/">Home</a> &middot; <a href="/login">Sign in</a></nav>
</main></div>`

let html = readFileSync(indexPath, 'utf8')
const target = '<div id="app"></div>'
if (!html.includes(target)) {
  console.error('prerender: "' + target + '" not found in dist/index.html — left unchanged')
  process.exit(0)
}
writeFileSync(indexPath, html.replace(target, snapshot))
console.log('prerender: injected static landing snapshot into dist/index.html')
