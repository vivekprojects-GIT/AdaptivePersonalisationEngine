"""APE client — calls the headless APE service (vg_mvp_v1.0) for SELECT+REWARD.

One call per adaptive turn:  POST {APE_BASE_URL}/turn
  in:  {user_id, session_id, classification.intent, signals[]}
  out: {selected_strategy, instruction{text,...}, turn_id, reward_applied, ...}

Design rules (see project discussion):
- APE is OPTIONAL infrastructure: if it is down, slow, or returns garbage,
  chat must keep working. Every failure path returns the NEUTRAL fallback.
- The caller never sends a turn id / previous strategy / reward — APE links
  the signals to its latest PENDING turn by (user, session) on its own.
- Uses 127.0.0.1 (not localhost) by default to avoid the Windows IPv6
  fallback penalty on every request.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

import time

APE_BASE_URL = os.getenv("APE_BASE_URL", "http://127.0.0.1:8099").rstrip("/")
APE_ENABLED = os.getenv("APE_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")
APE_TIMEOUT_SECONDS = float(os.getenv("APE_TIMEOUT_SECONDS", "2.5"))
# Shared secret for the engine's gated /admin + /analytics endpoints. Must match
# APE_ADMIN_TOKEN on the engine. /turn stays open and never needs it.
APE_ADMIN_TOKEN = os.getenv("APE_ADMIN_TOKEN", "").strip()

# When APE is unreachable, skip calling it for this long instead of paying the
# connect-timeout on EVERY message. One slow turn, then instant fallbacks.
APE_DOWN_COOLDOWN_SECONDS = float(os.getenv("APE_DOWN_COOLDOWN_SECONDS", "30"))
_down_until = 0.0

# What the adaptive lane used before APE — also the degraded-mode behavior.
NEUTRAL_STRATEGY = "neutral"
NEUTRAL_FORMAT_RULE = (
    "Answer naturally, clearly, and concisely. There is no required text format."
)


def neutral_turn(reason: str = "") -> dict:
    """The no-APE result. `ok=False` marks it as not bandit-served, so the
    caller must NOT count it as an APE-selected strategy."""
    return {
        "ok": False,
        "reason": reason,
        "strategy": NEUTRAL_STRATEGY,
        "format_rule": NEUTRAL_FORMAT_RULE,
        "turn_id": None,
        "reward_applied": None,
        "intent": None,
    }


def select_turn(user_id: str, session_id: str, intent: str, signals: list[str]) -> dict:
    """POST /turn. Returns a flat dict the server can use directly.

    Never raises — chat latency/availability must not depend on APE.
    """
    global _down_until
    if not APE_ENABLED:
        return neutral_turn("ape_disabled")
    if time.monotonic() < _down_until:
        return neutral_turn("ape_down_cooldown")

    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "classification": {"intent": intent or "unmapped"},
        "signals": [s for s in (signals or []) if s],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{APE_BASE_URL}/turn", data=data, method="POST")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=APE_TIMEOUT_SECONDS) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return neutral_turn(f"ape_http_{e.code}")
    except Exception as e:  # connection refused, timeout, bad JSON, ...
        _down_until = time.monotonic() + APE_DOWN_COOLDOWN_SECONDS
        return neutral_turn(f"ape_unreachable:{type(e).__name__}")

    instruction = body.get("instruction") or {}
    strategy = body.get("selected_strategy") or NEUTRAL_STRATEGY
    text = (instruction.get("text") or "").strip()
    if not text:
        # APE picked a strategy but served no instruction (shouldn't happen in
        # a healthy config) — degrade rather than send an empty rule.
        return neutral_turn("ape_empty_instruction")

    return {
        "ok": True,
        "reason": "",
        "strategy": strategy,
        "format_rule": text,
        "turn_id": body.get("turn_id"),
        "reward_applied": body.get("reward_applied"),
        "intent": (body.get("classification") or {}).get("intent"),
        "selection_method": body.get("selection_method"),
    }


def _get_json(path: str, timeout: float | None = None):
    """GET {APE_BASE_URL}{path} → parsed JSON, or None on any failure.

    Read-only helper for the Home-page playground/stats. Deliberately does NOT
    touch the down-cooldown: these calls are decorative, not on the chat path.
    """
    if not APE_ENABLED:
        return None
    try:
        req = urllib.request.Request(f"{APE_BASE_URL}{path}", method="GET")
        if APE_ADMIN_TOKEN:
            req.add_header("X-Admin-Token", APE_ADMIN_TOKEN)
        with urllib.request.urlopen(req, timeout=timeout or APE_TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def bandit_state(user_id: str, intent: str | None = None) -> list[dict]:
    """Per-user scoreboard rows (strategy, count, avg_reward, live UCB).

    Backed by APE's /admin/bandit-state, which returns ALL arms for a
    user-scoped query (including unpulled count=0 rows — that's how the
    playground shows round-robin progress). Never raises; [] on failure.
    """
    from urllib.parse import quote

    rows = _get_json(f"/admin/bandit-state?user_id={quote(user_id)}")
    if not isinstance(rows, list):
        return []
    out = []
    for r in rows:
        if intent and r.get("intent") != intent:
            continue
        out.append({
            "strategy": r.get("strategy"),
            "count": int(r.get("count", 0)),
            "avg_reward": float(r.get("avg_reward", 0.0)),
            "ucb": float(r.get("ucb", 0.0)),
        })
    return out


def platform_overview(days: int = 365) -> dict | None:
    """Aggregate live-engine stats for the Home proof band. None on failure."""
    # This aggregation scans a year of turns (~20s) — callers must cache it
    # and fetch off the request path (see server.playground_stats prewarm).
    return _get_json(f"/analytics/platform-overview?days={int(days)}", timeout=45.0)
