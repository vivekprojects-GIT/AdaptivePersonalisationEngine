"""Single-call combined response + widget generation — Claude-style architecture.

Instead of two sequential LLM calls (response then widget), this module
lets GPT-4 generate BOTH in one pass:

  Output format:
    <RESPONSE>
    [answer text here — follows primitive format rule]
    </RESPONSE>
    <WIDGET>
    [either complete self-contained HTML OR JSON UI schema (depending on WIDGET_MODE)]
    </WIDGET>

The parser splits these apart. Text goes to chat; widget payload goes to renderer.
This matches Claude's architecture: one model, one generation, no sequential delay.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Tuple

from . import config


def strip_widget_markdown_fences(raw: str) -> str:
    """Remove ```json ... ``` wrappers often emitted inside <WIDGET> despite instructions."""
    s = (raw or "").strip()
    if not s or "```" not in s:
        return s
    fence = re.search(r"```(?:json|html|javascript|js)?\s*(.*?)```", s, re.DOTALL | re.IGNORECASE)
    if fence:
        return fence.group(1).strip()
    return re.sub(r"```\w*", "", s).strip()


def parse_widget_schema_object(s: str) -> Any | None:
    """Parse first JSON value; tolerate leading/trailing prose via JSONDecoder.raw_decode."""
    s = strip_widget_markdown_fences(s).strip()
    if not s:
        return None
    dec = json.JSONDecoder()
    for start_ch in ("{", "["):
        idx = s.find(start_ch)
        if idx == -1:
            continue
        try:
            obj, _ = dec.raw_decode(s, idx)
            return obj
        except json.JSONDecodeError:
            continue
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


_BLOCK_TYPES = frozenset({"text", "kpi_row", "chart", "table", "action_row", "image", "stat_card", "progress", "badge_row"})

_TYPE_ALIASES: dict[str, str] = {
    "markdown": "text",
    "md": "text",
    "paragraph": "text",
    "rich_text": "text",
    "kpi": "kpi_row",
    "kpis": "kpi_row",
    "kpirow": "kpi_row",
    "metrics": "kpi_row",
    "metric_row": "kpi_row",
    "data_table": "table",
    "grid": "table",
    "actions": "action_row",
    "action": "action_row",
    "plot": "chart",
    "graph": "chart",
    "line_chart": "chart",
    "bar_chart": "chart",
    "photo": "image",
    "picture": "image",
    "img": "image",
    "illustration": "image",
}


def _normalize_layout_block(entry: Any) -> dict[str, Any]:
    """Turn primitives, malformed entries, and common aliases into valid block dicts."""
    if entry is None:
        return {"type": "text", "content": ""}
    if isinstance(entry, (str, int, float, bool)):
        return {"type": "text", "content": str(entry)}
    if isinstance(entry, list):
        return {"type": "text", "content": json.dumps(entry, ensure_ascii=False)}
    if not isinstance(entry, dict):
        return {"type": "text", "content": str(entry)}

    b: dict[str, Any] = dict(entry)
    raw_t = str(b.get("type") or "").strip().lower().replace("-", "_")
    t = _TYPE_ALIASES.get(raw_t, raw_t)
    if t in _BLOCK_TYPES:
        b["type"] = t
        return b

    items = b.get("items")
    if isinstance(items, list) and items:
        first = items[0]
        if isinstance(first, dict) and isinstance(first.get("label"), str):
            v = first.get("value")
            if isinstance(v, (str, int, float, bool)):
                b["type"] = "kpi_row"
                return b
    if isinstance(b.get("chart"), dict):
        b["type"] = "chart"
        return b
    src_val = b.get("src")
    if isinstance(src_val, str) and src_val.strip():
        b["type"] = "image"
        return b
    if isinstance(b.get("rows"), list):
        b["type"] = "table"
        return b
    if isinstance(b.get("buttons"), list):
        b["type"] = "action_row"
        return b
    for key in ("content", "body", "text", "markdown", "md"):
        v = b.get(key)
        if isinstance(v, str):
            return {"type": "text", "content": v}

    return {"type": "text", "content": json.dumps(b, ensure_ascii=False)}


def _sanitize_layout(layout: list[Any]) -> list[dict[str, Any]]:
    return [_normalize_layout_block(e) for e in layout]


# ── Registry-driven validation (keeps streaming; cleans the FINAL schema) ────
# Reads the SAME widget-registry.json used by the renderer to (1) drop block
# types the renderer can't draw, and (2) drop blocks with no renderable data
# (e.g. a chart with an unsupported kind or no data) — so the finalized widget
# never shows a blank/garbage block.
_REGISTRY_CACHE: dict[str, Any] | None = None


def _load_registry() -> dict[str, Any]:
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is None:
        try:
            _REGISTRY_CACHE = json.loads(Path(__file__).resolve().parent.parent / "frontend-vue" / "src" / "widget-registry.json")  # type: ignore[arg-type]
        except Exception:
            try:
                _REGISTRY_CACHE = json.loads(
                    (Path(__file__).resolve().parent.parent / "frontend-vue" / "src" / "widget-registry.json").read_text(encoding="utf-8")
                )
            except Exception:
                _REGISTRY_CACHE = {}
    return _REGISTRY_CACHE or {}


def _registry_block_types() -> set[str]:
    blocks = _load_registry().get("blocks") or []
    types = {str(b.get("type")).lower() for b in blocks if isinstance(b, dict) and b.get("type")}
    return types or set(_BLOCK_TYPES)


def _registry_chart_kinds() -> set[str]:
    for b in _load_registry().get("blocks") or []:
        if isinstance(b, dict) and str(b.get("type")).lower() == "chart":
            kinds = b.get("kinds")
            if isinstance(kinds, list) and kinds:
                return {str(k).lower() for k in kinds}
    return {"line", "bar", "area", "scatter", "heatmap", "pie", "donut"}


def _nonempty_list(v: Any) -> bool:
    return isinstance(v, list) and len(v) > 0


def _chart_has_data(chart: dict[str, Any]) -> bool:
    kind = str(chart.get("kind") or "line").lower()
    if kind not in _registry_chart_kinds():
        return False
    if kind == "heatmap":
        m = chart.get("matrix")
        return isinstance(m, list) and any(isinstance(r, list) and len(r) for r in m)
    if kind == "candlestick":
        return _nonempty_list(chart.get("candles"))
    if kind == "boxplot":
        return _nonempty_list(chart.get("boxes"))
    if kind in {"sankey", "graph", "flow", "flowchart", "process"}:
        return _nonempty_list(chart.get("links"))
    if kind in {"tree", "mindmap", "org", "orgchart"}:
        # Accept the same variants the renderer reads: root | tree | data | top-level node | items.
        root = chart.get("root") or chart.get("tree") or chart.get("data")
        if isinstance(root, list):
            root = root[0] if root else None
        if isinstance(root, dict) and (root.get("name") or root.get("label") or root.get("children")):
            return True
        if chart.get("name") or _nonempty_list(chart.get("children")) or _nonempty_list(chart.get("items")):
            return True
        return False
    if kind in {"pie", "donut", "funnel", "treemap", "sunburst", "waterfall", "gauge", "rose"}:
        if _nonempty_list(chart.get("items")):
            return True
        s = chart.get("series")
        return isinstance(s, list) and any(isinstance(x, dict) and x.get("values") for x in s)
    # line | bar | hbar | area | scatter | bubble | stacked | combo | histogram | radar
    # | timeseries | polar | parallel | themeriver | scatter3d | bar3d | line3d
    s = chart.get("series")
    if isinstance(s, list) and any(
        isinstance(x, dict) and isinstance(x.get("values"), list) and len(x.get("values")) for x in s
    ):
        return True
    # Fallback: the model may have used items (label/value) for a bar/line — still renderable.
    return _nonempty_list(chart.get("items"))


_NUMERIC_ARRAY_RE = re.compile(r"^\s*\[\s*-?\d+(\.\d+)?(\s*,\s*-?\d+(\.\d+)?)*\s*\]\s*$")


def _looks_like_json(s: str) -> bool:
    try:
        return isinstance(json.loads(s), (dict, list))
    except Exception:
        return s.strip()[:1] in "{["  # truncated JSON-ish


def _block_is_renderable(b: dict[str, Any]) -> bool:
    t = str(b.get("type") or "").lower()
    if t == "text":
        content = str(b.get("content") or "").strip()
        if not content or _NUMERIC_ARRAY_RE.match(content):
            return False  # bare numeric arrays (e.g. tic-tac-toe "[0,1,2]") are not prose
        # Drop text whose content is actually JSON (a block/layout the model stuffed in) —
        # it must never render as raw text in the UI.
        if content[:1] in "{[" and (
            re.search(r'"(?:type|layout|items|tone|label|series|chart)"\s*:', content)
            or _looks_like_json(content)
        ):
            return False
        return True
    if t == "kpi_row":
        items = b.get("items")
        return isinstance(items, list) and any(
            isinstance(it, dict) and str(it.get("value", "")).strip() for it in items
        )
    if t == "chart":
        chart = b.get("chart")
        return isinstance(chart, dict) and _chart_has_data(chart)
    if t == "table":
        rows = b.get("rows")
        return isinstance(rows, list) and len(rows) > 0
    if t == "action_row":
        btns = b.get("buttons")
        return isinstance(btns, list) and len(btns) > 0
    if t == "image":
        return bool(str(b.get("src") or "").strip())
    if t == "stat_card":
        items = b.get("items")
        return isinstance(items, list) and any(
            isinstance(it, dict) and str(it.get("value", "")).strip() for it in items
        )
    if t == "progress":
        items = b.get("items")
        return isinstance(items, list) and any(
            isinstance(it, dict) and it.get("value") is not None for it in items
        )
    if t == "badge_row":
        items = b.get("items")
        return isinstance(items, list) and any(
            isinstance(it, dict) and str(it.get("label", "")).strip() for it in items
        )
    return False


def _validate_layout_against_registry(layout: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop unknown block types and blocks with no renderable data."""
    valid_types = _registry_block_types()
    out: list[dict[str, Any]] = []
    for b in layout:
        if not isinstance(b, dict):
            continue
        if str(b.get("type") or "").lower() not in valid_types:
            continue
        if not _block_is_renderable(b):
            continue
        out.append(b)
    return out


def coerce_widget_schema_root(obj: Any) -> dict[str, Any] | None:
    """Ensure root has layout: [] (alias blocks/components; wrap bare arrays)."""
    if obj is None:
        return None
    if isinstance(obj, list):
        return {"version": "1.0", "layout": obj}
    if not isinstance(obj, dict):
        return None
    out = dict(obj)
    # Unwrap { "widget": { "layout": [...] } } or { "schema": {...} }
    if isinstance(out.get("widget"), dict):
        inner = dict(out.pop("widget"))
        out = {**out, **inner}
    if isinstance(out.get("schema"), dict):
        inner = dict(out.pop("schema"))
        out = {**out, **inner}
    if "layout" not in out or not isinstance(out.get("layout"), list):
        if isinstance(out.get("blocks"), list):
            out["layout"] = out["blocks"]
        elif isinstance(out.get("components"), list):
            out["layout"] = out["components"]
        elif isinstance(out.get("Layout"), list):
            out["layout"] = out.pop("Layout")
    # layout is a single block object (common model mistake)
    lay = out.get("layout")
    if isinstance(lay, dict) and lay.get("type"):
        out["layout"] = [lay]
    # Root is one block with no layout key
    if not isinstance(out.get("layout"), list) and out.get("type") in _BLOCK_TYPES:
        ver = out.pop("version", None)
        block = dict(out)
        out = {"version": str(ver or "1.0"), "layout": [block]}
    if isinstance(out.get("layout"), list):
        out["layout"] = _validate_layout_against_registry(_sanitize_layout(out["layout"]))
    return out


def widget_schema_json_is_valid(schema_str: str) -> bool:
    if not (schema_str or "").strip():
        return False
    try:
        o = json.loads(schema_str)
    except json.JSONDecodeError:
        return False
    return isinstance(o, dict) and isinstance(o.get("layout"), list)


def finalize_widget_schema_json(raw: str) -> str:
    """
    Normalize model output for the Vue renderer: strip fences, extract JSON, coerce layout.
    Returns a string safe for JSON.parse on the client (or best-effort stripped text).
    """
    raw = (raw or "").strip()
    if not raw:
        return ""
    obj = parse_widget_schema_object(raw)
    if obj is None:
        return strip_widget_markdown_fences(raw)
    coerced = coerce_widget_schema_root(obj)
    if coerced is None:
        return json.dumps(obj, ensure_ascii=False)
    return json.dumps(coerced, ensure_ascii=False)


# Hardcoded block list — used ONLY as the fallback when widget-registry.json is
# unreadable. The data-rule + trailer are SHARED with the live path (see below),
# so there is no duplicated guidance.
_FALLBACK_BLOCKS = """  - text:
    { "type": "text", "id": "...", "content": "..." }
  - kpi_row:
    { "type": "kpi_row", "id": "...", "items": [ { "label": "...", "value": "...", "tone": "positive|neutral|negative" }, ... ] }
  - chart (pick "kind" to fit the data; ONLY these kinds render):
    - line | bar | area | scatter  -> use "series" with [x, y] number pairs:
      { "type": "chart", "id": "...", "title": "...", "chart": { "kind": "line|bar|area|scatter", "x_label": "...", "y_label": "...", "series": [ { "name": "...", "values": [ [x, y], ... ] }, ... ] } }
    - heatmap (correlation matrix, confusion matrix, any grid of values) -> use labels + a 2D "matrix" (rows = y_labels, cols = x_labels):
      { "type": "chart", "id": "...", "title": "...", "chart": { "kind": "heatmap", "x_labels": ["A","B",...], "y_labels": ["A","B",...], "matrix": [ [1, 0.3, ...], [0.3, 1, ...], ... ] } }
    - pie | donut (composition / share of a whole) -> use "items":
      { "type": "chart", "id": "...", "title": "...", "chart": { "kind": "pie|donut", "items": [ { "label": "...", "value": 42 }, ... ] } }
    Do NOT invent other kinds. For a correlation matrix you MUST use kind "heatmap" with "matrix" (never a line/bar series).
  - table:
    { "type": "table", "id": "...", "title": "...", "columns": [ "Header A", "Header B", ... ], "rows": [ [ "cellA1", "cellB1" ], [ "cellA2", "cellB2" ], ... ] }
    "columns" MUST be an array of plain header STRINGS (e.g. ["Segment","Revenue (USD B)","% of Total"]) — NEVER objects like {"label":...,"key":...}. "rows" MUST be arrays of cell values in the SAME order as the columns.
  - action_row:
    { "type": "action_row", "id": "...", "buttons": [ { "id": "...", "label": "...", "intent": "..." }, ... ] }
  - image (photos, diagrams, icons, illustrations — any raster or SVG via URL/data URI):
    { "type": "image", "id": "...", "title": "...", "src": "https://... OR data:image/png;base64,...", "alt": "accessible description", "caption": "optional caption", "fit": "contain|cover" }
"""


# ── Registry-driven prompt vocabulary ───────────────────────────────────────
# Single source of truth: frontend-vue/src/widget-registry.json. The SAME file
# the Vue renderer uses to resolve block types is read here to generate the
# "supported block types" section of the prompt — so GENERATE and RENDER can
# never drift. Falls back to the static _JSON_WIDGET_RULE if the file is absent.
_REGISTRY_JSON_PATH = Path(__file__).resolve().parent.parent / "frontend-vue" / "src" / "widget-registry.json"

_JSON_RULE_PREAMBLE = """WIDGET JSON SCHEMA MODE (WIDGET_MODE=json):
- WIDGET WARRANT (DEFAULT TO AN EMPTY WIDGET — visuals are opt-in, not automatic):
  Produce a NON-EMPTY widget ONLY when at least one of these is clearly true:
    (a) the user EXPLICITLY asks for a visual — "plot/chart/graph this", "as a bar chart",
        "show me a …", "visualize …", or clicks a chart action button; OR
    (b) the answer is built around CONCRETE numbers the user supplied or explicitly asked to see
        (e.g. they pasted figures, or asked "show Q2 revenue by segment").
  In EVERY other case return an EMPTY widget (<WIDGET></WIDGET>). In particular:
    - Do NOT chart figures you had to estimate, recall, or hedge as "typical/approximate/around/roughly"
      — only chart real, given values. A fabricated chart is worse than no chart.
    - Do NOT auto-visualize a qualitative comparison, a conceptual explanation, a definition, a yes/no,
      or an opinion, even though you could invent a few numbers to fill a chart. The right home for a
      comparison is a markdown table or contrast in <RESPONSE>, not a widget.
  When unsure, return an EMPTY widget.
- The content inside <WIDGET> MUST be valid JSON (no markdown fences, no comments).
- Root object: { "version": "1.0", "layout": [ ... ] }
- layout is an ordered array of blocks (top-to-bottom).
- Supported block types ONLY (do not invent new ones):"""

# Data-source rule — strict (RAG on) vs. knowledge (RAG off). Selected in build_json_widget_rule().
_DATA_RULE_STRICT = """
NO FABRICATED DATA — ground every figure in the GROUNDING CONTEXT (applies to <RESPONSE> and <WIDGET>):
- Use ONLY figures that appear in the GROUNDING CONTEXT provided below (retrieved financial data),
  or numbers the user supplied in their message. Do NOT invent, estimate, recall from memory, or use
  "illustrative"/"mock"/"example"/"est." data.
- If the GROUNDING CONTEXT does not contain the figures needed to answer, say plainly in <RESPONSE>
  that you do not have that data, suggest what to ask instead, and return <WIDGET></WIDGET> (empty).
- NEVER label a chart or value "mock"/"illustrative"/"estimated" — if it is not in the context, do
  not render it. A widget must only ever show real values from the GROUNDING CONTEXT.
- Educational math demos (e.g. compound interest with user-given P/r/t) are fine — the user supplied
  the inputs.
"""

_DATA_RULE_KNOWLEDGE = """
DATA FROM YOUR KNOWLEDGE (applies to <RESPONSE> and <WIDGET>):
- Use your own world knowledge to provide concrete, realistic figures and DRAW the widget. You do NOT
  need a live source — give your best-known real-world values (e.g. company revenue, segments, market
  caps) and render the chart rather than refusing.
- If a number is approximate or from memory, you MAY briefly note that in <RESPONSE> (e.g. "approx",
  "FY2023"), but still render the widget.
- Do NOT fill charts with meaningless placeholder values (0,1,2,3 or random filler) — use genuine
  best-estimate numbers that reflect reality.
"""

_JSON_RULE_TRAILER = """
Data grounding (STRICT — the widget COPIES your <RESPONSE>, it never re-computes):
- IMPORTANT RULE — NO ROUNDING IN THE WIDGET. Take every widget value DIRECTLY from your <RESPONSE> and copy it EXACTLY, character-for-character. NEVER round, truncate, simplify, or reformat a number for the widget. If <RESPONSE> says $3.35T, the widget value is 3.35 — never 3.4, 3.3, or 3. If <RESPONSE> says 47.5, the widget is 47.5 — never 48 or 50. The widget number MUST be identical to the one written in <RESPONSE>.
- So: write the PRECISE figures in <RESPONSE> first (accurate, real, with their natural precision — do not round there either), then mirror those exact numbers into the widget.
- Use ONLY the exact numbers and labels stated in your <RESPONSE>. Do NOT invent values or add labels/values not written in <RESPONSE>.
- For category charts, "x_categories" MUST be the exact entity/segment names you named in <RESPONSE> (e.g. "Data Center", "Gaming") — NEVER 0, 1, 2. Each series value MUST equal the number in <RESPONSE>, aligned to those categories.
- KPI/stat/progress values and labels must also be the exact ones from <RESPONSE>.
- If <RESPONSE> does not state a number or its label, do not put it in the widget (state it in <RESPONSE> first, or omit it).

Honoring an explicitly requested chart type:
- If the user asks for a SPECIFIC chart type (e.g. "as a candlestick", "show a sankey", "pie chart") and it IS one of the supported kinds above, you MUST use exactly that kind — do not substitute another.
- If the requested chart type is NOT in the supported kinds (e.g. 3D surface, map/choropleth, gantt, renko, marimekko, etc.), DO NOT silently render a different chart, and DO NOT refuse the whole request. Instead, ANSWER FIRST, then decline only the chart:
  1. In <RESPONSE>, give a COMPLETE, natural written answer to the question (full prose/explanation with the real figures). Do NOT use the "### Analysis" numbered format here — no chart was rendered, so just answer in normal prose. Never reply with only a refusal.
  2. THEN, as the LAST line of <RESPONSE>, add the decline as a NOTE line. This is MANDATORY whenever you do not render a requested visual. EXACT FORMAT: the line must start with the literal 5 characters `NOTE:` followed by a space. Write it as PLAIN TEXT — do NOT bold it (no `**`), do NOT quote it (no `>`), do NOT bullet it (no `-`), do NOT put it inside a heading. Keep it warm and on-brand for the product "Vanguard", say it doesn't support that chart type YET, and suggest 1-3 supported kinds. Copy this shape exactly: `NOTE: Vanguard doesn't support Gantt charts yet — I can show this as a horizontal-bar timeline, a waterfall, or a stacked bar instead.`
  3. Return <WIDGET></WIDGET> (empty) and wait for them to choose a supported kind. Do NOT use blunt or technical wording like "broken", "incorrect output", or "I cannot render" — keep it courteous and reassuring.
- GENERAL (ALWAYS, no exceptions): any time you do NOT render a visualization the user asked for — unsupported kind, missing data, or you simply did not produce a widget — you MUST end <RESPONSE> with exactly one plain `NOTE:` line (same format as above) telling them why and what you CAN do instead. Never leave the user with a missing chart and no NOTE. If you produced the chart normally, do NOT add a NOTE line.
- Never pretend an unsupported type is supported, and never relabel a different chart as the requested type.
- CRITICAL: NEVER claim in <RESPONSE> that you rendered an unsupported chart. Do NOT write "here is ... rendered as a Gantt chart" (or 3D surface / choropleth / map / renko, etc.) — Gantt charts and maps are NOT supported. If the requested type is unsupported you MUST still answer the question in <RESPONSE>, then decline only the chart (the answer-first Vanguard message above) and return <WIDGET></WIDGET> (empty). Claiming you produced a widget you did not produce is forbidden.

Interactivity:
- action_row buttons are VISUALS-ONLY: each button must only offer to redraw the data ALREADY shown as a different supported chart kind (e.g. "Show as bar chart", "View as treemap", "Show as pie", "View as horizontal bars"). The button label is sent back as the next prompt, so it must be something you can definitely do with the data on screen.
- NEVER add action buttons that need data you may not have: no new tickers/companies, no new time periods, no "compare X vs Y", no growth/peers/forecasts, no "explain ...". If no alternative chart kind fits the data, omit the action_row.
- OUTPUT JSON ONLY. Never output HTML, <script>, <style>, <canvas>, raw markup, or code inside <WIDGET> — only the JSON schema above. There is no HTML mode.
- If something cannot be expressed with the supported block types (e.g. a playable game, live sliders), DO NOT invent HTML — return <WIDGET></WIDGET> (empty) and explain in <RESPONSE> instead. Never dump raw index arrays like `[0,1,2]`.
- For photographs, diagrams, or icons, use the `image` block with a valid https:// URL or a data: URI. Combine `image` with `text`, `chart`, and `table` blocks as needed.

Analysis goes in <RESPONSE>, the chart goes in <WIDGET> — never duplicate them:
- Whenever you produce a chart, the <RESPONSE> MUST contain proper DATA-ANALYST commentary — never show a bare, unexplained chart. Write the analysis in <RESPONSE> (NOT inside the widget): a heading line "### Analysis" then 3-4 NUMBERED points (each line: "1. ", "2. ", ...), wrapping the KEY figures/labels in **bold** (the UI highlights bold figures automatically — you never choose colors or styling). Example <RESPONSE>:
"Here's how NVIDIA's FY2024 revenue breaks down by segment.

### Analysis
1. **Data Center** at **$47.5B** is ~**78%** of total FY2024 revenue — the clear dominant segment.
2. It grew ~**3.2x YoY** (from **$15.0B**), driven by AI/HPC demand.
3. **Gaming** is a distant second at **$10.4B**; every other segment is under **$2B**.
4. Takeaway: revenue is heavily **concentrated in AI infrastructure**."
  Write like a financial/data analyst — specific and quantitative. Across the points cover: leader & laggard with values; the key gap/ratio/share/growth rate; the trend/notable change; any outlier or concentration; and a one-line "so what" takeaway. Use real numbers. NEVER write filler like "this chart shows the data" or "as you can see" — every point must carry a concrete insight. Always 3-4 points (not one).
- The "### Analysis" section appears ONLY when a chart is ACTUALLY rendered in a non-empty <WIDGET>. If the <WIDGET> is empty for ANY reason — you declined an unsupported chart, you lack the data, or the answer is text-only (a definition, concept, worded comparison, yes/no, advice, chat) — do NOT use the "### Analysis" heading or numbered analyst points. Instead write a COMPLETE, natural prose answer. Rule of thumb: NO rendered chart → NO "### Analysis" section, ever.
- Write a COMPLETE answer in <RESPONSE> — as full as the question needs; do NOT artificially truncate it. The <RESPONSE> is the written answer + analysis; the <WIDGET> is the visual.
- The <WIDGET> is the CHART ONLY (optionally a KPI row or a table when they add real value). Do NOT put the "### Analysis" text or narrative inside the widget — that lives in <RESPONSE>. Never write the same content in both places.
- Keep widget data compact: for charts that need many points (e.g. a bubble of countries), include at most ~15-20 points — enough to be representative, not exhaustive — so the widget stays small and renders fast without truncating.
- Add a `table` to the widget when it genuinely HELPS — e.g. exact reference figures or a breakdown the chart can't show. Do NOT add a table that merely restates a simple chart's few values (that is clutter).
- You MAY add a few KPI tiles for headline numbers when useful. Keep widget blocks ordered top-to-bottom by importance.
- Use `action_row` for obvious follow-up intents so the widget feels purposeful, not generic."""


# Fallback rule (registry unavailable) — assembled from the SAME shared parts the
# live path uses, so the guidance can never diverge from the registry-driven build.
_JSON_WIDGET_RULE = (
    _JSON_RULE_PREAMBLE + "\n" + _FALLBACK_BLOCKS + "\n" + _DATA_RULE_KNOWLEDGE + _JSON_RULE_TRAILER
)


def build_json_widget_rule() -> str:
    """Generate the WIDGET_MODE=json rule from the shared widget-registry.json."""
    try:
        data = json.loads(_REGISTRY_JSON_PATH.read_text(encoding="utf-8"))
        blocks = data.get("blocks") if isinstance(data, dict) else None
        if not isinstance(blocks, list) or not blocks:
            return _JSON_WIDGET_RULE.strip()
        entries: list[str] = []
        for b in blocks:
            if not isinstance(b, dict):
                continue
            t = str(b.get("type") or "").strip()
            when = str(b.get("whenToUse") or "").strip()
            spec = b.get("spec")
            if not t or not spec:
                continue
            spec_lines = spec if isinstance(spec, list) else [str(spec)]
            body = "\n".join("    " + str(ln) for ln in spec_lines)
            header = f"  - {t}" + (f" — {when}" if when else "") + ":"
            entries.append(f"{header}\n{body}")
        if not entries:
            return _JSON_WIDGET_RULE.strip()
        # Strict grounding when RAG is on; otherwise let the model use its own knowledge.
        data_rule = _DATA_RULE_STRICT if getattr(config, "USE_RAG", False) else _DATA_RULE_KNOWLEDGE
        return (
            _JSON_RULE_PREAMBLE + "\n" + "\n".join(entries) + "\n" + data_rule + _JSON_RULE_TRAILER
        )
    except Exception:
        return _JSON_WIDGET_RULE.strip()



_OUTPUT_CONTRACT_STRICT = """
OUTPUT CONTRACT (STRICT — MUST FOLLOW)
You MUST return these sections in this exact order:

<RESPONSE>
...text...
</RESPONSE>
<WIDGET>
...widget OR empty...
</WIDGET>

Rules:
- Never omit the <WIDGET> tags, but content may be empty when a widget is not warranted.
- If widget is warranted, return a valid interactive widget (not placeholders).
- If widget is not warranted (simple chit-chat / conceptual text-only), return exactly <WIDGET></WIDGET>.
If you fail to follow this contract, the system will break.
"""

def is_social_or_greeting_turn(user_message: str) -> bool:
    """Short greeting/thanks/goodbye only — no required format (used for prompt routing only)."""
    t = (user_message or "").strip()
    if not t or len(t) > 160:
        return False
    tl = " ".join(t.lower().split())
    if "?" in t and len(t) > 25:
        return False
    if re.fullmatch(
        r"(hi|hello|hey|yo|sup|hiya|bye|goodbye|ok|okay|k|cheers|thx|ty|thanks|thank you)"
        r"([!?.])*",
        tl,
    ):
        return True
    if re.fullmatch(
        r"(thanks|thank you)( a lot| so much| again)?([!?.])*",
        tl,
    ):
        return True
    if re.fullmatch(
        r"(good )?(morning|afternoon|evening|night)([!?.])*",
        tl,
    ):
        return True
    if re.fullmatch(r"got it([!?.])*", tl):
        return True
    if re.fullmatch(
        r"(hi|hello|hey)\s+(there|everyone|all|team)([!?.])*",
        tl,
    ):
        return True
    return False


def build_combined_system_prompt(
    strategy_id: str,
    format_rule: str,
    primitive_extra_context: str,
    user_message: str,
    grounding_context: str = "",
    forbidden_components: list[str] | None = None,
    required_components: list[str] | None = None,
) -> str:
    """
    Build the combined system prompt for a single LLM call that outputs
    both the response text and the widget HTML together.

    Args:
        strategy_id:              selected strategy name (e.g. 'comparison_table')
        format_rule:              primitive format instruction for response text
        primitive_extra_context:  widget layout instructions from primitives.json
        forbidden_components:     component names the widget MUST NOT use
        required_components:      component names the widget MUST use
    """
    widget_block = ""
    if primitive_extra_context:
        widget_block = f"""
## Widget layout instructions (follow these exactly)
{primitive_extra_context}
"""

    constraint_block = ""
    if forbidden_components:
        names = ", ".join(forbidden_components)
        constraint_block += (
            "\n## FORBIDDEN — do NOT use these components inside <WIDGET>\n"
            f"{names}\n"
            "If your widget uses any of these, it will be rejected and replaced.\n"
        )
    if required_components:
        names = ", ".join(required_components)
        constraint_block += (
            "\n## REQUIRED — your <WIDGET> MUST contain these components\n"
            f"{names}\n"
            "If your widget is missing any of these, it will be rejected and replaced.\n"
        )

    social_only = is_social_or_greeting_turn(user_message)
    if social_only:
        response_rule_line = (
            "GENERAL / SOCIAL TURN — ignore Strategy and Rule below. "
            "Reply in 1–2 short, natural sentences only. No bullets, tables, numbered lists, or fenced code blocks."
        )
    else:
        response_rule_line = "Treat this as a style hint for <RESPONSE> (do not be rigid)."

    social_turn_banner = ""
    if social_only:
        social_turn_banner = """
═══════════════════════════════════════════════════════
GENERAL QUESTION — GREETING / THANKS / GOODBYE
═══════════════════════════════════════════════════════
The user's message is only a greeting, thanks, acknowledgement, or goodbye.
- <RESPONSE>: Brief, friendly, natural text. Do NOT apply the Strategy or Rule shown below.
- <WIDGET>: Return exactly <WIDGET></WIDGET> (empty). No chart, no dashboard, no placeholder HTML.
═══════════════════════════════════════════════════════
"""

    # Components-only / JSON schema mode is the only mode. The widget vocabulary,
    # warrant rubric, strict grounding, and decline rules all come from the registry
    # (build_json_widget_rule → widget-registry.json). No HTML, no external libraries.
    widget_format_line = "JSON UI schema ONLY (no HTML) for the widget"
    widget_rules_header = "WIDGET RULES — for the JSON schema inside <WIDGET>"
    widget_rules_body = build_json_widget_rule()

    combined_max_tokens = getattr(config, "COMBINED_MAX_TOKENS", 7500)
    token_limit_block = f"""
TOKEN LIMIT — you have ~{combined_max_tokens} tokens total for <RESPONSE> + <WIDGET>.
- Write a COMPLETE <RESPONSE> (full written answer + the ### Analysis) AND a complete <WIDGET>. Do not stop mid-widget or truncate either one.
- The <RESPONSE> can be as long as the question genuinely needs — do not pad, but do not cut it short either. If the budget is ever tight, trim widget DATA points (keep ~15-20), never the analysis.
"""

    if grounding_context.strip():
        grounding_block = (
            "\n═══════════════════════════════════════════════════════\n"
            "GROUNDING CONTEXT — retrieved financial data (the ONLY source for your figures)\n"
            "═══════════════════════════════════════════════════════\n"
            "Use ONLY numbers/labels that appear below. Do not add figures from memory.\n\n"
            f"{grounding_context.strip()}\n"
        )
    elif getattr(config, "USE_RAG", False):
        # RAG on but nothing relevant retrieved → decline rather than fabricate.
        grounding_block = (
            "\n═══════════════════════════════════════════════════════\n"
            "GROUNDING CONTEXT — none retrieved\n"
            "═══════════════════════════════════════════════════════\n"
            "No financial data was retrieved for this query. You do NOT have figures for it: "
            "say so plainly in <RESPONSE> and return <WIDGET></WIDGET> (empty). Do NOT use memory or estimates.\n"
        )
    else:
        # RAG off → knowledge mode (the data rule lets the model use its own figures).
        grounding_block = ""

    # The STABLE prefix (identical every turn for a given config) is placed first so
    # it can be prompt-cached; the per-turn TAIL (grounding, strategy, user-specific)
    # follows after the cache boundary marker. The Anthropic path caches the prefix.
    stable_prefix = f"""You are an expert AI assistant. Each turn you produce a written answer AND an OPTIONAL interactive widget built ONLY from a fixed set of UI components defined below — there is NO HTML and NO external charting libraries.
Output style: No emojis. Neat, clean, professional — in both <RESPONSE> text and <WIDGET>.
{token_limit_block}
{_OUTPUT_CONTRACT_STRICT}

For every turn you produce TWO sections in one generation: the <RESPONSE> text first, then the <WIDGET>. The widget may be empty when a visual is not warranted (see WIDGET WARRANT below). Never describe a widget you did not produce (e.g. don't write "the dashboard below" and then return an empty widget).

RENDER NOW — when (and ONLY when) a visual is warranted per WIDGET WARRANT above, never defer or ask permission:
- If the user EXPLICITLY asks for a chart/visualization and you can build it from concrete data in this conversation, you MUST output the NON-EMPTY <WIDGET> in THIS turn. (If you'd have to invent the numbers, render nothing and say so instead — see the data rule.)
- HARD RULE: if your <RESPONSE> says or implies a chart exists ("Here is a … chart", "the chart below", "as shown"), the <WIDGET> MUST contain that chart as a valid block. Writing "Here is a rose chart …" and then leaving <WIDGET> empty is a contract violation. Either produce the populated widget, or change the wording to not claim a chart.
- Supported chart kinds (e.g. rose, pie, bar, line, treemap, sankey…) MUST be rendered — only decline for genuinely UNSUPPORTED kinds (gantt, map, 3D surface). For a supported kind, never return an empty widget.
- NEVER reply with "I will plot…", "let me show…", "shall I…", or ask "which dataset?" when the conversation already implies the data — just render the chart now with a sensible default.
- For a clear visualization request, do NOT respond with clarifying questions (even if the Strategy suggests asking) — produce the chart. Only ask a question if the request is genuinely ambiguous AND no reasonable default exists.
- The Strategy only shapes the short framing TEXT; it must NEVER stop you from producing the widget. Only return an empty widget when you truly lack the data or the requested chart type is unsupported (and then say so plainly).

═══════════════════════════════════════════════════════
OUTPUT FORMAT — always use exactly this structure
═══════════════════════════════════════════════════════
<RESPONSE>
[Your answer here — follow the RESPONSE FORMAT RULE below]
</RESPONSE>
<WIDGET>
[{widget_format_line}]
</WIDGET>

<RESPONSE> is prose for the user — NEVER put JSON, a widget schema, block objects, or code fences in it. All structured data goes ONLY inside <WIDGET>.
NEVER draw visuals as text in <RESPONSE>: no ASCII charts/bars, no tree drawings (├──, └──), no aligned-column tables-as-art. The <WIDGET> is the ONLY place a visualization lives. For a hierarchy/mind map, put it in a chart block with "kind":"tree"|"mindmap"|"org" and a "root", not as text.
CRITICAL — Primitives vs Widget (never confuse these):
- The RESPONSE FORMAT RULE shown below applies ONLY to <RESPONSE> (text format: bullets, table, prose, etc.). It does NOT constrain <WIDGET>.
- <WIDGET> is SEPARATE and INDEPENDENT. Widget choice depends on the content of your <RESPONSE>, not on the text format.

═══════════════════════════════════════════════════════
{widget_rules_header}
═══════════════════════════════════════════════════════
{widget_rules_body}"""

    dynamic_tail = f"""{social_turn_banner}
{grounding_block}
═══════════════════════════════════════════════════════
RESPONSE FORMAT RULE — {response_rule_line}
═══════════════════════════════════════════════════════
Strategy: {strategy_id}
Rule: {format_rule}
Do not mention this rule. Do not add <WIDGET> inside <RESPONSE>.
{widget_block}
{constraint_block}"""

    return f"{stable_prefix}\n{config.SYSTEM_CACHE_BOUNDARY}\n{dynamic_tail}"


def build_combined_user_prompt(
    user_message: str,
    history: list[dict],
    max_history: int = 4,
) -> str:
    """Build the user-turn prompt including conversation history."""
    ctx: list[str] = []
    for turn in history[-max_history:]:
        u = turn.get("user", "")
        a = turn.get("assistant", "")
        if u:
            ctx.append(f"User: {u}")
        if a:
            # Strip any <WIDGET>...</WIDGET> from stored history to keep it concise.
            a_clean = re.sub(r"<WIDGET>.*?</WIDGET>", "", a, flags=re.DOTALL).strip()
            ctx.append(f"Assistant: {a_clean}")
    ctx.append(f"User: {user_message}")
    return "\n".join(ctx)


def strip_leaked_widget_json(text: str) -> str:
    """Remove any widget JSON the model leaked into the prose response.

    The <RESPONSE> is meant to be human text only. Sometimes the model dumps a
    block object / layout JSON (or a ```json fence) into it. We strip:
      - fenced code blocks whose body looks like widget JSON, and
      - bare {...}/[...] blobs that contain widget keys ("type"/"layout"/"version"),
        balanced or truncated — so raw JSON can NEVER reach the client.
    """
    s = text or ""
    # 1) fenced blocks that look like widget JSON
    def _fence(m: "re.Match") -> str:
        inner = (m.group(1) or "").strip()
        if inner[:1] in "[{" and re.search(r'"(?:type|layout|items|tone|series|chart|version)"', inner):
            return ""
        return m.group(0)
    s = re.sub(r"```[\w-]*\s*([\s\S]*?)```", _fence, s)
    # 2) bare JSON blobs starting with a widget key
    out = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch in "{[":
            head = s[i:i + 400]
            if re.search(r'"(?:type|layout|version)"\s*:', head):
                close = "}" if ch == "{" else "]"
                depth = 0
                in_str = False
                esc = False
                j = i
                while j < n:
                    c = s[j]
                    if in_str:
                        if esc:
                            esc = False
                        elif c == "\\":
                            esc = True
                        elif c == '"':
                            in_str = False
                    elif c == '"':
                        in_str = True
                    elif c == ch:
                        depth += 1
                    elif c == close:
                        depth -= 1
                        if depth == 0:
                            j += 1
                            break
                    j += 1
                # balanced → skip the blob; truncated → drop to end
                i = j if depth == 0 else n
                continue
        out.append(ch)
        i += 1
    return "".join(out).strip()


def parse_combined_output(raw: str) -> Tuple[str, str]:
    """
    Parse model combined output into (response_text, widget_payload).

    Returns:
        (response_text, widget_payload)
        Either can be empty string if the tag is missing or parsing fails.
    """
    response_text = ""
    widget_payload = ""

    # Extract <RESPONSE>...</RESPONSE>
    resp_match = re.search(r"<RESPONSE>(.*?)</RESPONSE>", raw, re.DOTALL | re.IGNORECASE)
    if resp_match:
        response_text = resp_match.group(1).strip()
    else:
        # Fallback: everything before <WIDGET> is the response
        widget_start = raw.find("<WIDGET>")
        if widget_start == -1:
            widget_start_upper = raw.upper().find("<WIDGET>")
            if widget_start_upper != -1:
                widget_start = widget_start_upper
        if widget_start > 0:
            response_text = raw[:widget_start].strip()
        else:
            response_text = raw.strip()

    # Extract <WIDGET>...</WIDGET> — JSON schema only (no HTML mode).
    widget_match = re.search(r"<WIDGET>(.*?)</WIDGET>", raw, re.DOTALL | re.IGNORECASE)
    if widget_match:
        raw_widget = widget_match.group(1).strip()
        widget_payload = finalize_widget_schema_json(raw_widget)

    # The response is human prose only — never let leaked widget JSON reach the client.
    response_text = strip_leaked_widget_json(response_text)

    return response_text, widget_payload
