"""LLM helpers for Anthropic and OpenAI-compatible endpoints.

This module centralizes HTTP calls and provides small helpers used by the
server to call either Anthropic (Claude) or an OpenAI-compatible API.
"""

import json
import urllib.request
import urllib.error
import time
import concurrent.futures
from typing import Tuple

from . import config

try:
    import anthropic  # type: ignore
except Exception:  # pragma: no cover
    anthropic = None
    _anthropic_import_error = "import_failed"
else:
    _anthropic_import_error = ""


def _post_json_url(url: str, payload: dict, headers: dict | None = None, timeout: int = 120) -> dict:
    """POST JSON and return decoded response.

    Raises the underlying urllib errors to the caller for handling.
    """
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Mozilla/5.0")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json_url(url: str, headers: dict | None = None, timeout: int = 15) -> dict:
    """GET from a URL and return the decoded JSON response.

    Args:
        url: Target URL.
        headers: Optional dict of additional HTTP headers.
        timeout: Request timeout in seconds.

    Returns:
        Decoded JSON response as a dict.
    """
    req = urllib.request.Request(url, method="GET")
    req.add_header("User-Agent", "Mozilla/5.0")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _anthropic_temp_kwargs(temperature: float) -> dict:
    """Return {'temperature': ...} unless the model rejects it (e.g. opus-4-8)."""
    mode = str(getattr(config, "ANTHROPIC_SEND_TEMPERATURE", "auto")).lower()
    model = getattr(config, "ANTHROPIC_MODEL", "")
    if mode in {"0", "false", "no", "off"}:
        return {}
    if mode == "auto" and ("opus-4-8" in model or "opus-4-7" in model):
        return {}
    return {"temperature": temperature}


def _strip_cache_boundary(system):
    """Remove the cache-boundary marker, returning a clean single string."""
    boundary = getattr(config, "SYSTEM_CACHE_BOUNDARY", "")
    if isinstance(system, str) and boundary and boundary in system:
        return system.replace(boundary, "\n").strip()
    return system


def _anthropic_system_param(system):
    """Turn the system string into a cached-prefix + tail block list for Anthropic
    prompt caching. Splits on the cache boundary; the stable prefix gets an
    `ephemeral` cache_control so repeat calls bill it ~90% cheaper. Falls back to a
    plain (boundary-stripped) string when caching is off or no boundary is present.
    """
    boundary = getattr(config, "SYSTEM_CACHE_BOUNDARY", "")
    if not isinstance(system, str) or not boundary or boundary not in system:
        return system
    prefix, _, tail = system.partition(boundary)
    if getattr(config, "ANTHROPIC_PROMPT_CACHE", False):
        return [
            {"type": "text", "text": prefix.rstrip(), "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": tail.lstrip()},
        ]
    return (prefix.rstrip() + "\n" + tail.lstrip()).strip()


def _anthropic_extra_kwargs() -> dict:
    """Build extra_headers / extra_body for Fast Mode + Opus effort.

    Returned as a single dict so callers can splat it into messages.create().
    On any API rejection, callers retry with {} (no extras).
    """
    headers: dict = {}
    body: dict = {}
    if getattr(config, "ANTHROPIC_FAST_MODE_ENABLED", False):
        headers["anthropic-beta"] = getattr(config, "ANTHROPIC_FAST_MODE_BETA", "fast-mode-2026-02-01")
        body["speed"] = getattr(config, "ANTHROPIC_FAST_MODE_SPEED", "fast")
    effort = getattr(config, "ANTHROPIC_EFFORT", "")
    if effort:
        body["effort"] = effort
    kw: dict = {}
    if headers:
        kw["extra_headers"] = headers
    if body:
        kw["extra_body"] = body
    return kw


def call_openai_compat(
    prompt: str,
    system: str,
    timeout: int = 120,
    max_tokens: int = 400,
    temperature: float = 0.2,
) -> Tuple[str, float, str]:
    """Call an OpenAI-compatible chat/completions endpoint.

    Returns (text, elapsed_seconds, mode).
    """
    if not config.OPENAI_API_KEY:
        raise RuntimeError("Missing OPENAI_API_KEY env var")
    t0 = time.time()
    payload = {
        "model": config.OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": _strip_cache_boundary(system)},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if getattr(config, "OPENAI_REASONING_EFFORT", ""):
        payload["reasoning_effort"] = config.OPENAI_REASONING_EFFORT
    headers = {"Authorization": f"Bearer {config.OPENAI_API_KEY}"}
    data = _post_json_url(f"{config.OPENAI_BASE_URL}/chat/completions", payload, headers=headers, timeout=timeout)
    text = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
    return (text or str(data)), round(time.time() - t0, 1), "openai_compat"


def stream_openai_compat(
    prompt: str,
    system: str,
    timeout: int = 120,
    max_tokens: int = 400,
    temperature: float = 0.2,
):
    """Yield content deltas (token-by-token) from an OpenAI-compatible endpoint.

    Reads the SSE `data: {...}` lines and yields each choice's delta.content.
    Any `reasoning_content` deltas are ignored, so internal thinking never
    reaches the user. Yields:  str chunks of answer text.
    """
    if not config.OPENAI_API_KEY:
        raise RuntimeError("Missing OPENAI_API_KEY env var")

    payload = {
        "model": config.OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": _strip_cache_boundary(system)},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    if getattr(config, "OPENAI_REASONING_EFFORT", ""):
        payload["reasoning_effort"] = config.OPENAI_REASONING_EFFORT
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{config.OPENAI_BASE_URL}/chat/completions", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {config.OPENAI_API_KEY}")
    req.add_header("Accept", "text/event-stream")
    # Groq sits behind Cloudflare, which 403s (error 1010) the default
    # Python-urllib User-Agent. A normal UA is required for the stream to open.
    req.add_header("User-Agent", "Mozilla/5.0")

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "ignore").strip()
            if not line or not line.startswith("data:"):
                continue
            body = line[5:].strip()
            if body == "[DONE]":
                break
            try:
                obj = json.loads(body)
            except Exception:
                continue
            delta = ((obj.get("choices") or [{}])[0] or {}).get("delta") or {}
            chunk = delta.get("content")
            if chunk:
                yield str(chunk)


def call_anthropic(
    prompt: str,
    system: str,
    timeout: int = 120,
    max_tokens: int = 400,
    temperature: float = 0.2,
) -> Tuple[str, float, str]:
    """Call Anthropic Messages API (Claude) and return (text, elapsed_seconds, mode)."""
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("Missing ANTHROPIC_API_KEY env var")
    if anthropic is None:
        raise RuntimeError(f"Missing `anthropic` package. Import error: {_anthropic_import_error}")

    fast_kwargs = _anthropic_extra_kwargs()
    temp_kwargs = _anthropic_temp_kwargs(temperature)
    system_param = _anthropic_system_param(system)

    t0 = time.time()
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    # Anthropic SDK handles timeouts internally; we keep our signature for parity.
    # Some SDK/provider combinations may ignore the SDK-level timeout and hang
    # for a long time. Enforce a wall-clock timeout so the server can respond
    # with an error instead of freezing the UI.
    def _create(with_fast: dict) -> object:
        return client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system_param,
            messages=[{"role": "user", "content": prompt}],
            timeout=timeout,
            **temp_kwargs,
            **with_fast,
        )

    msg = None
    try:
        ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            fut = ex.submit(_create, fast_kwargs)
            msg = fut.result(timeout=timeout)
        finally:
            # Do not block waiting for a stuck SDK call to finish.
            ex.shutdown(wait=False, cancel_futures=True)
    except concurrent.futures.TimeoutError as e:
        raise RuntimeError(f"Anthropic request timed out after {timeout}s") from e
    except Exception:
        # If Fast Mode beta isn't accepted for this request/model/SDK version, retry normally.
        ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            fut = ex.submit(_create, {})
            msg = fut.result(timeout=timeout)
        finally:
            ex.shutdown(wait=False, cancel_futures=True)

    # `content` is typically a list of blocks; concatenate everything we can.
    # This avoids missing parts of the model output if some blocks don't expose
    # `.text` (e.g., non-text block representations).
    texts: list[str] = []
    for block in getattr(msg, "content", []) or []:
        t = getattr(block, "text", None)
        if t is not None:
            texts.append(str(t))
        else:
            texts.append(str(block))
    text = "\n".join([t for t in texts if t]).strip()
    if not text:
        # Fallback: stringify response object.
        text = str(msg).strip()

    return text, round(time.time() - t0, 1), "anthropic"


def stream_anthropic(
    prompt: str,
    system: str,
    timeout: int = 120,
    max_tokens: int = 400,
    temperature: float = 0.2,
):
    """Yield Anthropic content deltas (token-by-token).

    Yields:
        str chunks of text from `content_block_delta`.
    """
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("Missing ANTHROPIC_API_KEY env var")
    if anthropic is None:
        raise RuntimeError(f"Missing `anthropic` package. Import error: {_anthropic_import_error}")

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    fast_kwargs = _anthropic_extra_kwargs()
    temp_kwargs = _anthropic_temp_kwargs(temperature)
    system_param = _anthropic_system_param(system)

    try:
        with client.messages.stream(
            model=config.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system_param,
            messages=[{"role": "user", "content": prompt}],
            timeout=timeout,
            **temp_kwargs,
            **fast_kwargs,
        ) as stream:
            for event in stream:
                if getattr(event, "type", None) == "content_block_delta":
                    delta = getattr(event, "delta", None)
                    chunk = getattr(delta, "text", None) if delta is not None else None
                    if chunk:
                        yield str(chunk)
    except Exception:
        # Retry without fast-mode params.
        with client.messages.stream(
            model=config.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system_param,
            messages=[{"role": "user", "content": prompt}],
            timeout=timeout,
            **temp_kwargs,
        ) as stream:
            for event in stream:
                if getattr(event, "type", None) == "content_block_delta":
                    delta = getattr(event, "delta", None)
                    chunk = getattr(delta, "text", None) if delta is not None else None
                    if chunk:
                        yield str(chunk)


def openai_health(timeout: int = 10) -> dict:
    """Return basic health info for an OpenAI-compatible endpoint."""
    try:
        headers = {"Authorization": f"Bearer {config.OPENAI_API_KEY}"} if config.OPENAI_API_KEY else {}
        data = _get_json_url(f"{config.OPENAI_BASE_URL}/models", headers=headers, timeout=timeout)
        ids = [m.get("id") for m in (data.get("data") or []) if isinstance(m, dict)]
        return {"ok": True, "reachable": True, "models": ids[:25]}
    except Exception as e:
        return {"ok": False, "reachable": False, "models": [], "error": str(e)}


def anthropic_health() -> dict:
    """Return basic health info for Anthropic configuration.

    Anthropic does not expose a simple unauthenticated models endpoint like OpenAI.
    We keep this as a lightweight config check.
    """
    ok = bool(getattr(config, "ANTHROPIC_API_KEY", "") and getattr(config, "ANTHROPIC_MODEL", ""))
    return {"ok": ok, "reachable": ok, "model": getattr(config, "ANTHROPIC_MODEL", "")}
