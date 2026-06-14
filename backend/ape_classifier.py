"""Pre-turn classifier for the APE integration.

One cheap LLM call per adaptive turn, BEFORE calling APE. Returns:

    {
      "intent":  one of APE's closed intent set (else "unmapped"),
      "signals": text-detected APE signals about the PREVIOUS answer,
      "lane":    "answer" | "widget_redraw"
    }

Lane router (the rule that protects the bandit):
- "widget_redraw" = the message ONLY asks to redraw the previous visual as a
  different chart kind ("pie chart instead", "show as treemap"). The server
  SKIPS the APE call entirely for these turns: there is no new prose answer,
  so creating a PENDING turn record would corrupt APE's reward attribution,
  and a chart-kind complaint must never become a text-format signal.
- "answer" = everything else (a new question, possibly carrying reaction
  signals about the previous answer).

Failure policy: any error → {"intent": "unmapped", "signals": [], "lane":
"answer"} — the chat must never break because classification failed.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import re

from . import config
from . import llm

# APE's closed intent set (vg_mvp_v1.0 ape/strategies/catalog.py). Anything
# else is coerced to "unmapped" — same rule APE itself applies.
APE_INTENTS = [
    "Decision",
    "Explanation",
    "Comparison",
    "Instructional",
    "Definitional",
    "Evaluation",
]

# Text-detectable subset of APE's signal catalog (thumbs are UI events and
# arrive via /api/rate, not from text).
TEXT_SIGNALS = [
    "format_change_request",
    "format_praise_explicit",
    "content_correction",
    "it_worked_statement",
    "deeper_question",
    "reask_same_question",
]

CLASSIFIER_MODEL = os.getenv("APE_CLASSIFIER_MODEL", "claude-haiku-4-5-20251001")
# Keep the pre-stream budget tight: a slow classify delays time-to-first-token.
CLASSIFIER_TIMEOUT = float(os.getenv("APE_CLASSIFIER_TIMEOUT", "8"))

FALLBACK = {"intent": "unmapped", "signals": [], "lane": "answer"}

_SYSTEM = """You are a strict classifier for a chat orchestrator. Output ONLY a JSON object — no prose, no code fences.

Classify the user's NEW message on three things:

1) "intent" — what kind of question/request the NEW message is. Exactly one of:
   Decision (which option should I pick / what should I do),
   Explanation (help me understand a concept),
   Comparison (X vs Y, differences, side-by-side),
   Instructional (how do I do it, steps),
   Definitional (what is X, short meaning),
   Evaluation (judge/review/assess something I present),
   unmapped (greetings, chit-chat, pure reactions, data lookups, anything else).

2) "signals" — reactions in the NEW message about the PREVIOUS assistant answer. Zero or more of:
   format_change_request  — asks to reshape the TEXT: shorter/longer, bullets, paragraph, summary, "as a table" (text). NOT chart-kind changes.
   format_praise_explicit — explicitly praises the text's SHAPE ("love this table", "this layout is perfect").
   content_correction     — says a fact/number/claim was wrong.
   it_worked_statement    — says the previous answer worked/helped ("perfect, thanks", "that fixed it").
   deeper_question        — the new message builds directly on the previous answer (follow-up depth).
   reask_same_question    — repeats/rephrases the SAME question because the answer didn't land.
   Empty list if none. A plain new question on a new topic carries no signals.

3) "lane" — route the turn:
   "widget_redraw" — the message ONLY asks to redraw the previous VISUAL as another chart kind (pie/bar/line/area/treemap/scatter/graph...), with no new question. Chart-kind requests are NEVER format_change_request.
   "answer" — everything else.

Disambiguation rules:
- Chart/plot/graph kind words (pie, bar, line, treemap, ...) target the WIDGET → no text-format signal. If that's all the message does → lane widget_redraw.
- "as a table": if PREV_WIDGET_PRESENT is true, it means the data widget → widget_redraw; if false, it's a text format_change_request.
- "make it shorter / simpler / bullets" targets the TEXT → format_change_request, lane answer.
- Mixed (reaction + new question) → lane answer, include the signals, intent of the NEW question.

Output exactly: {"intent": "...", "signals": [...], "lane": "..."}"""


def _extract_json(text: str) -> dict | None:
    """Tolerant JSON extraction (strips fences, finds the first {...} block)."""
    if not text:
        return None
    t = text.strip()
    t = re.sub(r"^```[\w-]*\s*", "", t)
    t = re.sub(r"\s*```$", "", t).strip()
    m = re.search(r"\{.*\}", t, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _normalize(raw: dict | None) -> dict:
    if not isinstance(raw, dict):
        return dict(FALLBACK)
    intent = str(raw.get("intent") or "").strip()
    if intent not in APE_INTENTS:
        intent = "unmapped"
    signals = [s for s in (raw.get("signals") or []) if s in TEXT_SIGNALS]
    lane = raw.get("lane")
    if lane not in ("answer", "widget_redraw"):
        lane = "answer"
    # Belt-and-braces: a redraw turn never carries text-format signals.
    if lane == "widget_redraw":
        signals = [s for s in signals if s != "format_change_request"]
    return {"intent": intent, "signals": signals, "lane": lane}


def _call_anthropic_small(prompt: str) -> str:
    import anthropic  # same optional dep llm.py uses

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def _create():
        return client.messages.create(
            model=CLASSIFIER_MODEL,
            max_tokens=150,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            timeout=CLASSIFIER_TIMEOUT,
        )

    ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        msg = ex.submit(_create).result(timeout=CLASSIFIER_TIMEOUT)
    finally:
        ex.shutdown(wait=False, cancel_futures=True)
    parts = []
    for block in getattr(msg, "content", []) or []:
        t = getattr(block, "text", None)
        if t:
            parts.append(str(t))
    return "\n".join(parts).strip()


def classify(
    message: str,
    *,
    prev_widget_present: bool = False,
    prev_user_message: str = "",
) -> dict:
    """Classify one incoming adaptive-chat message. Never raises."""
    prompt = (
        f"PREV_WIDGET_PRESENT: {str(bool(prev_widget_present)).lower()}\n"
        f"PREVIOUS_USER_MESSAGE: {(prev_user_message or '')[:400]}\n"
        f"NEW_MESSAGE: {(message or '')[:2000]}"
    )
    try:
        mode = (config.ADAPTIVE_LLM_MODE or config.LLM_MODE).lower()
        if mode == "anthropic" and config.ANTHROPIC_API_KEY:
            text = _call_anthropic_small(prompt)
        else:
            text, _, _ = llm.call_openai_compat(
                prompt, _SYSTEM, timeout=int(CLASSIFIER_TIMEOUT), max_tokens=150, temperature=0.0
            )
        return _normalize(_extract_json(text))
    except Exception:
        return dict(FALLBACK)
