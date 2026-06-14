---
sdk: docker
app_port: 7860
---
# Adaptive Presentation Engine — Demo

A chat app where Claude answers a question **and** generates an interactive widget for it.
Widgets are built **only from the app's own UI components** (a registry), as JSON — **no
LLM-generated HTML, no iframe, no external chart libraries**. Charts render with bundled
ECharts.

> **Architecture:** see [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) for the full registry →
> prompt-menu → synthesizer → validate → components pipeline.

## Project structure

```
ape/
├── app.py                        # entry point (Hugging Face Spaces runs this)
├── Dockerfile  requirements.txt
├── .env.example                  # template (copy to .env; .env is gitignored)
├── backend/                      # FastAPI app
│   ├── config.py                 # env, LLM modes, paths
│   ├── server.py                 # FastAPI: auth, /api/chat[_stream], serves SPA
│   ├── llm.py                    # Anthropic + OpenAI-compatible calls
│   ├── engine.py                 # in-memory per-user conversation state
│   ├── combined_prompt.py        # builds the combined prompt; registry → menu; validation
│   └── db.py / auth.py
├── rag_finance/                  # optional RAG module (registry-driven)
├── frontend/                     # Vue 3 + Vite + TypeScript SPA (the live UI)
│   ├── src/
│   │   ├── widget-registry.json  # SINGLE SOURCE: block types + 33 chart kinds + data shapes
│   │   ├── lib/widgetRegistry.ts # type → Vue component map (RENDER)
│   │   ├── components/WidgetRegistryRenderer.vue  # parses widget JSON → <component :is>
│   │   └── components/widgets/*.vue               # TextBlock, KpiRow, ChartBlock, ...
│   └── dist/                     # built SPA (served by the backend in prod)
├── data/                         # runtime data + seeds
│   ├── skills.md                 # chart/widget guidance injected into prompts
│   └── user_primitives.json      # admin primitives store
└── docs/
    ├── ARCHITECTURE.md
    └── APE_v2_End_to_End.docx
```

## What it shows
- **Components-only widgets** — 9 block types + 33 chart kinds, all from the registry
- **Adaptive vs Baseline comparison** — governed components next to raw LLM HTML
- **Live SSE streaming** — block-by-block widget rendering without flicker
- **Deterministic styling** — colors/format owned by components, never by the LLM

---

## Setup (5 minutes)

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
# (numpy, python-dotenv, anthropic — server is built-in, no Flask)
```

### 2. Configure environment
Copy the example env file and add your API keys:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and/or ANTHROPIC_API_KEY
```

This app supports:
- OpenAI-compatible providers (via `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`)
- Anthropic Claude (via `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`)

### 3. Run the demo server
```bash
python app.py
```

### 4. Open in browser
```
http://localhost:5051   # or PORT from env (Docker uses 7860)
```

---

## How to demo it

1. **Ask a data question** (e.g. "Top 5 tech companies by market cap as a bar chart") — the
   Adaptive pane renders a governed component widget; Baseline shows the raw-HTML contrast
2. **Try multi-visual questions** — multiple chart blocks stream in block-by-block
3. **Ask for an unsupported chart** (e.g. a Gantt) — full text answer + a red NOTE decline
4. **Download a widget** as standalone interactive HTML or JSON
5. **Clear chat / Reset session** from the sidebar

---

## Architecture notes (for Q&A)
- **Single combined LLM call** — `<RESPONSE>` + `<WIDGET>` in one stream (low latency)
- **Registry as single source of truth** — generate/validate/render can never drift
- **Prompt caching** — stable system prefix cached (90% cheaper input on hits)
- **Circuit breaker** — LLM timeouts fail fast gracefully
