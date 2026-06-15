"""FastAPI server for the Adaptive Presentation Engine backend.

Endpoints
---------
- GET  /                : Vue SPA entry
- GET  /api/healthz     : process liveness (no external calls)
- GET  /api/health      : LLM connectivity check (use sparingly)
- POST /api/chat        : adaptive chat (non-streaming) — APE picks the text format
- POST /api/chat_stream : adaptive chat (SSE streaming — Claude-style)
- POST /api/rate        : thumbs on the last answer (queued APE signal)
- POST /api/reset       : clear user session

SSE stream events (`evt.type`)
------------------------------
- start           : stream opened (emitted first)
- response_delta  : token chunk inside <RESPONSE>
- widget_start    : model opened <WIDGET>
- widget_delta    : raw token chunk inside <WIDGET> (live, Claude-style)
- done            : final assembled payload (canonical response + polished widget)
"""

from __future__ import annotations

import json
import os
import re
import time
import threading
import uuid
from typing import Iterable

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from . import config, llm
from . import ape_client, ape_classifier
from .combined_prompt import (
    build_combined_system_prompt,
    build_combined_user_prompt,
    finalize_widget_schema_json,
    parse_combined_output,
    strip_leaked_widget_json,
    widget_schema_json_is_valid,
)
from .engine import engine
from .auth import (
    authenticate_login,
    create_access_token,
    decode_access_token,
    get_or_create_google_user,
    get_user_by_id,
    get_user_by_email,
    register_user,
    seed_users_from_db,
    update_password,
)
from . import db as persistence
from .widget_stream import parse_combined_stream


# ---------------------------------------------------------------------------
# Auth plumbing
# ---------------------------------------------------------------------------

bearer_scheme = HTTPBearer(auto_error=False)

_password_reset_lock = threading.Lock()
_password_reset_tokens: dict[str, dict] = {}
_PASSWORD_RESET_TTL_SECONDS = int(os.getenv("PASSWORD_RESET_TTL_SECONDS", "900"))


_GUEST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{4,64}$")


def require_user_id(
    credentials=Depends(bearer_scheme),
    x_guest_id: str | None = Header(default=None),
) -> str:
    """Resolve the caller's identity. Auth is OPTIONAL (guest mode):

    1. A valid bearer token wins (registered account).
    2. Otherwise the browser's X-Guest-Id header becomes a stable per-browser
       identity ("guest_<id>") — so APE's per-user learning still works
       without any login.
    3. No header at all → the shared "guest" identity.

    This endpoint never 401s; an expired/invalid token simply degrades to
    guest instead of breaking the chat.
    """
    if credentials is not None and getattr(credentials, "credentials", None):
        try:
            return decode_access_token(credentials.credentials)
        except Exception:
            pass  # expired/invalid token → continue as guest
    gid = (x_guest_id or "").strip()
    if _GUEST_ID_RE.fullmatch(gid):
        return f"guest_{gid}"
    return "guest"


def _is_admin_user(user_id: str) -> bool:
    """
    Admin check. Previous behavior silently promoted everyone to admin when
    ADMIN_* config was missing; that's a production footgun. We now require
    explicit admin configuration — no config means no admin.
    """
    if not getattr(config, "ADMIN_CONFIGURED", False):
        return False

    if user_id in set(map(str, getattr(config, "ADMIN_USER_IDS", []) or [])):
        return True

    rec = get_user_by_id(user_id)
    if not rec:
        return False

    username_n = (rec.username or "").strip().lower()
    email_n = (rec.email or "").strip().lower()
    return username_n in {u.lower() for u in (config.ADMIN_USERNAMES or [])} or email_n in {
        e.lower() for e in (config.ADMIN_EMAILS or [])
    }


def require_admin_user_id(user_id: str = Depends(require_user_id)) -> str:
    if not _is_admin_user(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user_id


# ---------------------------------------------------------------------------
# Public API vocabulary. Internal engine names (selection methods, the
# exploration score) never reach the browser — we translate them at the
# response boundary so the wire payload carries neutral product language.
# ---------------------------------------------------------------------------
_PUBLIC_METHOD = {"ucb": "learned", "round_robin": "exploring", "fallback": "fallback"}


def _public_method(method):
    """Map an internal selection-method name to its public label."""
    return _PUBLIC_METHOD.get(method, method)


def _public_arms(arms):
    """Reshape per-format scoreboard rows for the browser: the internal score
    field is exposed only as a neutral `confidence` value."""
    out = []
    for a in arms or []:
        out.append({
            "strategy": a.get("strategy"),
            "count": a.get("count"),
            "avg_reward": a.get("avg_reward"),
            "confidence": a.get("ucb"),
        })
    return out


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

def sse_pack(evt: dict) -> str:
    """Pack a JSON event into an SSE data frame."""
    return f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"


def _json_layout_is_only_numeric_index_arrays(schema_str: str) -> bool:
    """
    Detect bogus JSON widgets where every block is text like '[0,1,2]' (e.g. tic-tac-toe
    win lines) instead of real UI. Those pass structural validation but are not widgets.
    """
    import json as _json
    import re as _re

    try:
        o = _json.loads(schema_str)
    except _json.JSONDecodeError:
        return False
    layout = o.get("layout")
    if not isinstance(layout, list) or len(layout) < 2:
        return False
    pat = _re.compile(r"^\s*\[\s*\d+(\s*,\s*\d+)*\s*\]\s*$")
    for item in layout:
        if not isinstance(item, dict):
            return False
        if str(item.get("type", "")).lower() != "text":
            return False
        if not pat.match(str(item.get("content", ""))):
            return False
    return True


def _dispatch_json_mode_widget(widget_payload_raw: str) -> tuple[str, str, int, str]:
    """
    STRICT components-only: always resolve to a JSON schema rendered by the registry
    components. The HTML escape-hatch is DISABLED — model-generated HTML is never
    rendered. Returns (widget_schema, widget_html, widget_height, widget_debug_tag);
    widget_html is always "".
    """
    raw = (widget_payload_raw or "").strip()
    if not raw:
        return "", "", 0, ""

    finalized = finalize_widget_schema_json(raw)
    if widget_schema_json_is_valid(finalized) and not _json_layout_is_only_numeric_index_arrays(finalized):
        return finalized, "", 0, "json_schema_ok"
    if _json_layout_is_only_numeric_index_arrays(finalized):
        return "", "", 0, "json_degenerate_layout"
    return finalized, "", 0, "json_schema_invalid"


# NOTE: widget generation is NOT gated by keyword matching. The synthesizer LLM
# decides per turn whether a widget helps AND whether it can populate it with real
# values using the allowed block types (see the warrant rubric in combined_prompt).
# A keyword list both over-fires ("bar exam") and misses ("how has revenue moved?"),
# and it can't know whether the data exists to fill a chart — the model can.


# ---------------------------------------------------------------------------
# Request/response schemas
# ---------------------------------------------------------------------------

class ChatReq(BaseModel):
    uid: str | None = None
    message: str


class RateReq(BaseModel):
    direction: str  # "up" | "down" — thumbs on the last adaptive answer


class ResetReq(BaseModel):
    uid: str | None = None


class PrimitiveCreateReq(BaseModel):
    name: str
    instruction: str


class PrimitiveUpdateReq(BaseModel):
    name: str
    instruction: str


class AuthRegisterReq(BaseModel):
    username: str
    email: str
    password: str


class AuthLoginReq(BaseModel):
    username_or_email: str
    password: str


class GoogleAuthReq(BaseModel):
    credential: str


class ForgotPasswordReq(BaseModel):
    email: str


class ResetPasswordReq(BaseModel):
    token: str
    new_password: str


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Adaptive Presentation Engine")

app.add_middleware(
    CORSMiddleware,
    # allow_credentials=True is incompatible with "*" per CORS spec;
    # keep it False since we use bearer tokens, not cookies.
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.on_event("startup")
def _on_startup():
    persistence.init_db()

    # RAG: only when enabled — ingest the financial corpus into ChromaDB on first boot
    # (the binary store is not shipped). When USE_RAG is off, skip entirely (no model download).
    if getattr(config, "USE_RAG", False):
        try:
            from rag_finance.retriever import _load as _rag_load
            from rag_finance.ingest import ingest as _rag_ingest
            col, _ = _rag_load()
            if col is None or col.count() == 0:
                stats = _rag_ingest()
                print(f"[rag] ingested {stats.get('documents')} financial docs into ChromaDB")
        except Exception as e:
            print(f"[rag] ingest skipped: {e}")

    if getattr(config, "ADMIN_CONFIGURED", False) and config.ADMIN_USERNAME and config.ADMIN_PASSWORD and config.ADMIN_EMAIL:
        try:
            register_user(username=config.ADMIN_USERNAME, email=config.ADMIN_EMAIL, password=config.ADMIN_PASSWORD)
        except Exception:
            pass

    try:
        users = persistence.load_users_from_db()
        seed_users_from_db(users)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Static / SPA
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    # API-only when the frontend build isn't present (it's deployed separately).
    if not config.INDEX_HTML.exists():
        return JSONResponse({
            "service": "APE backend", "status": "ok", "mode": "api-only",
            "note": "The web app is hosted separately; call the /api/* endpoints.",
        })
    html = config.INDEX_HTML.read_bytes()
    return HTMLResponse(content=html, media_type="text/html; charset=utf-8")


@app.get("/api/healthz")
def healthz():
    """Process liveness — cheap, no external dependencies."""
    return {"ok": True}


@app.get("/api/health")
def health():
    if config.LLM_MODE == "openai_compat":
        h = llm.openai_health()
        return {
            "server": "ok",
            "mode": config.LLM_MODE,
            "openai_base_url": config.OPENAI_BASE_URL,
            "model": config.OPENAI_MODEL,
            **h,
        }
    if config.LLM_MODE == "anthropic":
        h = llm.anthropic_health()
        return {"server": "ok", "mode": config.LLM_MODE, **h}
    return {
        "server": "ok",
        "mode": config.LLM_MODE,
        "ok": False,
        "reachable": False,
        "error": "Unsupported LLM_MODE (expected openai_compat or anthropic)",
    }


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.post("/api/auth/register")
def auth_register(req: AuthRegisterReq):
    try:
        rec = register_user(username=req.username, email=req.email, password=req.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    token = create_access_token(user_id=rec.user_id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"user_id": rec.user_id, "username": rec.username, "email": rec.email},
    }


@app.post("/api/auth/login")
def auth_login(req: AuthLoginReq):
    rec = authenticate_login(username_or_email=req.username_or_email, password=req.password)
    if not rec:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user_id=rec.user_id)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/api/auth/google")
def auth_google(req: GoogleAuthReq):
    """Sign in / sign up with a Google ID token (from Google Identity Services).

    The frontend obtains a one-time ID token (JWT) from Google and posts it here
    as `credential`. We validate it against Google's tokeninfo endpoint, confirm
    the audience matches our own OAuth client and the email is verified, then
    find-or-create the account and issue our own session token.
    """
    client_id = getattr(config, "GOOGLE_CLIENT_ID", "")
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login is not configured",
        )

    cred = (req.credential or "").strip()
    if not cred:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing credential")

    from urllib.parse import quote

    try:
        info = llm._get_json_url(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={quote(cred)}", timeout=10
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google credential")

    iss = str(info.get("iss") or "")
    if iss not in ("accounts.google.com", "https://accounts.google.com"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Untrusted token issuer")
    if str(info.get("aud") or "") != client_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token audience mismatch")

    email = (info.get("email") or "").strip()
    email_verified = str(info.get("email_verified") or "").lower() in ("true", "1")
    if not email or not email_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google email not verified")

    try:
        rec = get_or_create_google_user(email=email, name=info.get("name") or info.get("given_name"))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    token = create_access_token(user_id=rec.user_id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"user_id": rec.user_id, "username": rec.username, "email": rec.email},
    }


@app.post("/api/auth/forgot-password")
def auth_forgot_password(req: ForgotPasswordReq):
    """Dev/demo only. Do NOT return the reset token to the caller in production."""
    email = (req.email or "").strip()
    user = get_user_by_email(email)

    if not user:
        return {"ok": True}

    token = uuid.uuid4().hex
    now = int(time.time())
    expires = now + _PASSWORD_RESET_TTL_SECONDS
    with _password_reset_lock:
        _password_reset_tokens[token] = {"user_id": user.user_id, "expires": expires}

    # Expose reset token only in development to ease local testing.
    expose_token = (os.getenv("ENV", "development") or "development").lower() != "production"
    if expose_token:
        return {"ok": True, "reset_token": token}
    return {"ok": True}


@app.post("/api/auth/reset-password")
def auth_reset_password(req: ResetPasswordReq):
    token = (req.token or "").strip()
    new_password = (req.new_password or "").strip()

    if not token or not new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="token and new_password required")

    now = int(time.time())
    with _password_reset_lock:
        rec = _password_reset_tokens.get(token)
        if not rec:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
        if int(rec.get("expires") or 0) < now:
            _password_reset_tokens.pop(token, None)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
        user_id = str(rec.get("user_id") or "")
        _password_reset_tokens.pop(token, None)

    try:
        ok = update_password(user_id=user_id, new_password=new_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {"ok": True}


@app.get("/api/me")
def me(user_id: str = Depends(require_user_id)):
    if user_id.startswith("guest"):
        return {"user_id": user_id, "username": "Guest", "email": "", "is_admin": False}
    rec = get_user_by_id(user_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "user_id": rec.user_id,
        "username": rec.username,
        "email": rec.email,
        "is_admin": _is_admin_user(rec.user_id),
    }


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

@app.get("/api/primitives")
def list_primitives(user_id: str = Depends(require_admin_user_id)):
    return {"items": persistence.list_user_primitives(user_id)}


@app.post("/api/primitives")
def create_primitive(req: PrimitiveCreateReq, user_id: str = Depends(require_admin_user_id)):
    name = (req.name or "").strip()
    inst = (req.instruction or "").strip()
    if not name or not inst:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name and instruction are required")
    row = persistence.create_user_primitive(user_id=user_id, name=name, instruction=inst)
    return {"item": row}


@app.put("/api/primitives/{prim_id}")
def update_primitive(prim_id: int, req: PrimitiveUpdateReq, user_id: str = Depends(require_admin_user_id)):
    name = (req.name or "").strip()
    inst = (req.instruction or "").strip()
    if not name or not inst:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name and instruction are required")
    row = persistence.update_user_primitive(user_id=user_id, prim_id=int(prim_id), name=name, instruction=inst)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Primitive not found")
    return {"item": row}


@app.delete("/api/primitives/{prim_id}")
def delete_primitive(prim_id: int, user_id: str = Depends(require_admin_user_id)):
    ok = persistence.delete_user_primitive(user_id=user_id, prim_id=int(prim_id))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Primitive not found")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Conversation history
# ---------------------------------------------------------------------------

@app.get("/api/conversation")
def conversation(limit: int = 20, user_id: str = Depends(require_user_id)):
    uid = user_id
    lim = int(limit)
    lim = max(1, min(lim, 50))

    def _pairs_from_msgs(msgs: list[dict]) -> list[dict]:
        out: list[dict] = []
        last_user: str | None = None
        for m in msgs:
            if m.get("role") == "user":
                last_user = str(m.get("content") or "")
            elif m.get("role") == "assistant":
                if last_user is None:
                    continue
                out.append(
                    {
                        "user": last_user,
                        "assistant": str(m.get("content") or ""),
                        "widget_html": str(m.get("widget_html") or ""),
                        "widget_schema": str(m.get("widget_schema") or ""),
                        "widget_height": int(m.get("widget_height") or 0),
                    }
                )
                last_user = None
        return out[-lim:]

    adaptive_msgs = persistence.get_recent_conversation_messages(user_id=uid, pane="adaptive", limit=lim * 4)
    adaptive_pairs = _pairs_from_msgs(adaptive_msgs)

    if not adaptive_pairs:
        adaptive_user = engine.get_user(uid)
        adaptive_pairs = (adaptive_user.get("history") or [])[-lim:]

    return {"adaptive": {"history": adaptive_pairs}}


# ---------------------------------------------------------------------------
# Background persistence (off the hot path)
# ---------------------------------------------------------------------------

def _persist_after_response(
    *,
    user_id: str,
    uid: str,
    msg: str,
    response: str,
    strategy: str | None,
    elapsed: float | None,
    widget_present: bool,
    pane: str,
    widget_html: str = "",
    widget_schema: str = "",
    widget_height: int = 0,
) -> None:
    """Persist the conversation log after the response has been sent.

    Runs in FastAPI BackgroundTasks so HTTP latency is not gated by SQLite commits.
    """
    try:
        persistence.log_conversation_message(
            user_id=user_id, pane=pane, role="user", content=msg,
            strategy=strategy if pane == "adaptive" else None,
        )
        persistence.log_conversation_message(
            user_id=user_id, pane=pane, role="assistant", content=response,
            strategy=strategy if pane == "adaptive" else None,
            elapsed=elapsed, widget=widget_present,
            widget_html=widget_html or "",
            widget_schema=widget_schema or "",
            widget_height=int(widget_height or 0),
        )
    except Exception:
        # Persistence failures must never surface to the user.
        pass



# ---------------------------------------------------------------------------
# Adaptive chat — non-streaming
# ---------------------------------------------------------------------------

def _build_adaptive_prompt(uid: str, msg: str):
    """Shared prompt-assembly step for adaptive endpoints.

    APE integration (v2). Per turn:
      1. classify the message (intent + reaction signals + lane) — one cheap LLM call
      2. lane "widget_redraw" → SKIP APE (no new prose answer: a chart-kind swap
         must not create a junk PENDING turn or emit a text-format signal);
         reuse the previous turn's strategy/format_rule so the prose stays stable.
      3. lane "answer" → POST APE /turn with queued UI signals (thumbs from
         /api/rate) + text-detected signals. APE banks the reward for the
         PREVIOUS answer (it finds it by (user, session) itself) and SELECTs
         the text format for THIS answer. On any APE failure → neutral fallback.
    """
    user = engine.get_user(uid)

    cls = ape_classifier.classify(
        msg,
        prev_widget_present=bool(user.get("last_widget_present")),
        prev_user_message=user.get("last_message") or "",
    )

    ape = None
    signals_sent: list[str] = []
    if cls["lane"] == "widget_redraw":
        # Sticky: same text rules as the answer still on screen. APE untouched —
        # its latest PENDING slip stays the true target for future signals.
        strat = user.get("last_strategy") or ape_client.NEUTRAL_STRATEGY
        format_rule = user.get("last_format_rule") or ape_client.NEUTRAL_FORMAT_RULE
        ape = ape_client.neutral_turn("widget_redraw_skip")
    else:
        signals_sent = list(dict.fromkeys((user.get("pending_signals") or []) + cls["signals"]))
        ape = ape_client.select_turn(uid, user["session_id"], cls["intent"], signals_sent)
        user["pending_signals"] = []
        strat = ape["strategy"]
        format_rule = ape["format_rule"]
        if ape["ok"]:
            user["last_strategy"] = strat
            user["last_format_rule"] = format_rule

    prim_block = ""
    if _is_admin_user(uid):
        user_prims = persistence.list_user_primitives(uid)
        if user_prims:
            prim_lines = []
            for p in user_prims:
                nm = str(p.get("name") or "").strip()
                inst = str(p.get("instruction") or "").strip()
                if nm and inst:
                    prim_lines.append(f"- {nm}: {inst}")
            if prim_lines:
                prim_block = "\n\n## User primitives (follow these as constraints)\n" + "\n".join(prim_lines) + "\n"

    # RAG: when ON, retrieve clean financial figures (entity-gated) → GROUNDING CONTEXT.
    # When OFF, no context → the model fills figures from its own knowledge.
    grounding_context = ""
    if config.USE_RAG:
        try:
            from rag_finance.retriever import retrieve as _rag_retrieve
            rag = _rag_retrieve(msg, k=6)
            if rag.get("relevant") and rag.get("chunks"):
                grounding_context = "\n\n".join(rag["chunks"])
        except Exception as e:
            print(f"[rag] retrieve failed: {e}")

    combined_system = build_combined_system_prompt(
        strategy_id=strat,
        format_rule=format_rule,
        primitive_extra_context=(getattr(config, "SKILLS_CONTENT", "") or "") + prim_block,
        user_message=msg,
        grounding_context=grounding_context,
        forbidden_components=None,
        required_components=None,
    )
    combined_prompt = build_combined_user_prompt(user_message=msg, history=user["history"])

    return {
        "user": user,
        "strat": strat,
        "format_rule": format_rule,
        "combined_system": combined_system, "combined_prompt": combined_prompt,
        # APE telemetry for payloads/logs (never required by the render path).
        "ape": {
            "served_by_ape": bool(ape and ape.get("ok")),
            "reason": (ape or {}).get("reason", ""),
            "turn_id": (ape or {}).get("turn_id"),
            "reward_applied": (ape or {}).get("reward_applied"),
            "selection_method": _public_method((ape or {}).get("selection_method")),
            "intent": cls["intent"],
            "lane": cls["lane"],
            "signals_sent": signals_sent,
        },
    }


def _post_done_payload(
    *,
    ctx: dict,
    elapsed: float | None,
    mode: str,
    response: str,
    widget_html: str,
    widget_schema: str,
    widget_height: int,
    widget_debug: str,
    raw_preview: str,
):
    return {
        "response": response,
        "format_rule": ctx["format_rule"],
        "strategy": ctx.get("strat", ""),
        "ape": ctx.get("ape", {}),
        "elapsed": elapsed,
        "llm_mode": mode,
        "widget_html": widget_html or "",
        "widget_schema": widget_schema or "",
        "widget_height": widget_height,
        "widget_debug": widget_debug,
        "widget_raw_preview": raw_preview if not (widget_html or widget_schema) else "",
    }


@app.post("/api/chat")
def chat(req: ChatReq, bg: BackgroundTasks, user_id: str = Depends(require_user_id)):
    uid = user_id
    msg = (req.message or "").strip()
    if not msg:
        return JSONResponse({"error": "empty message"}, status_code=400)

    ctx = _build_adaptive_prompt(uid, msg)

    combined_max_tokens = getattr(config, "COMBINED_MAX_TOKENS", 4000)
    combined_timeout = getattr(config, "COMBINED_TIMEOUT_SECONDS", 45)

    try:
        adapt_mode = (config.ADAPTIVE_LLM_MODE or config.LLM_MODE).lower()
        if adapt_mode == "openai_compat":
            raw_combined, elapsed, mode = llm.call_openai_compat(
                ctx["combined_prompt"], ctx["combined_system"],
                timeout=combined_timeout, max_tokens=combined_max_tokens, temperature=0.2,
            )
        elif adapt_mode == "anthropic":
            raw_combined, elapsed, mode = llm.call_anthropic(
                ctx["combined_prompt"], ctx["combined_system"],
                timeout=combined_timeout, max_tokens=combined_max_tokens, temperature=0.2,
            )
        else:
            raise RuntimeError("Unsupported ADAPTIVE_LLM_MODE (expected openai_compat or anthropic)")
    except Exception as e:
        return JSONResponse({"error": f"LLM error: {str(e)}"}, status_code=500)

    if not raw_combined:
        return JSONResponse({"error": "LLM returned empty response. Check model/service."}, status_code=500)

    response, widget_payload_raw = parse_combined_output(raw_combined)
    if not response:
        response = raw_combined.strip()

    widget_html = ""  # components-only: always empty; kept for payload/DB compatibility
    widget_schema = ""
    widget_height = 0
    widget_debug = ""
    raw_preview = ""

    if widget_payload_raw:
        widget_schema, widget_html, widget_height, tag = _dispatch_json_mode_widget(widget_payload_raw)
        widget_debug = tag or ""
    else:
        # No <WIDGET> payload — the model judged this turn better as text-only (or declined).
        # That is a valid outcome; render prose with no widget card.
        widget_debug = "combined_no_schema"
        raw_preview = (raw_combined or "")[:800]

    user = ctx["user"]
    user["history"].append({"user": msg, "assistant": response})
    user["history"] = user["history"][-20:]
    user["last_message"] = msg
    user["last_response"] = response
    user["msg_count"] += 1
    user["last_widget_present"] = bool(widget_html or widget_schema)

    payload = _post_done_payload(
        ctx=ctx, elapsed=elapsed, mode=mode, response=response,
        widget_html=widget_html, widget_schema=widget_schema,
        widget_height=widget_height, widget_debug=widget_debug, raw_preview=raw_preview,
    )

    bg.add_task(
        _persist_after_response,
        user_id=user_id, uid=uid, msg=msg, response=response,
        strategy=ctx.get("strat"), elapsed=elapsed,
        widget_present=bool(widget_html or widget_schema), pane="adaptive",
        widget_html=widget_html or "",
        widget_schema=widget_schema or "",
        widget_height=int(widget_height or 0),
    )

    return payload


# ---------------------------------------------------------------------------
# Adaptive chat — SSE streaming (Claude-style live widget streaming)
# ---------------------------------------------------------------------------

@app.post("/api/chat_stream")
def chat_stream(req: ChatReq, bg: BackgroundTasks, user_id: str = Depends(require_user_id)):
    uid = user_id
    msg = (req.message or "").strip()
    if not msg:
        return JSONResponse({"error": "empty message"}, status_code=400)

    ctx = _build_adaptive_prompt(uid, msg)
    combined_max_tokens = getattr(config, "COMBINED_MAX_TOKENS", 4000)
    combined_timeout = getattr(config, "COMBINED_TIMEOUT_SECONDS", 45)
    adapt_mode = (config.ADAPTIVE_LLM_MODE or config.LLM_MODE).lower()

    def gen() -> Iterable[str]:
        t0 = time.time()

        # Initial event — UI clears its "thinking" state immediately.
        yield sse_pack({
            "type": "start",
            "format_rule": ctx["format_rule"],
            "strategy": ctx.get("strat", ""),
            "ape": ctx.get("ape", {}),
            "elapsed": None,
        })

        widget_html = ""  # components-only: always empty; kept for payload/DB compatibility
        widget_schema = ""
        widget_height = 0
        widget_debug = ""
        response = ""
        mode = adapt_mode
        elapsed_out: float | None = None
        widget_payload_raw = ""

        try:
            if adapt_mode == "anthropic":
                stream = llm.stream_anthropic(
                    ctx["combined_prompt"], ctx["combined_system"],
                    timeout=combined_timeout, max_tokens=combined_max_tokens, temperature=0.2,
                )

                # Stream response tokens LIVE for low latency. The model can occasionally leak
                # widget JSON into <RESPONSE>; the frontend strips it at display time, and the
                # final `response` below is also stripped — so no JSON persists, without the lag
                # of buffering the whole answer first.
                response_closed = False
                for event in parse_combined_stream(
                    stream,
                    emit_response_deltas=True,
                    emit_widget_deltas=True,
                ):
                    etype = event[0]
                    if etype == "response_delta":
                        yield sse_pack({"type": "response_delta", "delta": event[1]})
                    elif etype == "response_closed":
                        response_closed = True
                        response = strip_leaked_widget_json(event[1])
                    elif etype == "widget_start":
                        yield sse_pack({"type": "widget_start"})
                    elif etype == "widget_delta":
                        # LIVE widget streaming — Claude-style.
                        yield sse_pack({"type": "widget_delta", "delta": event[1]})
                    elif etype == "complete":
                        if not response_closed:
                            response = strip_leaked_widget_json(event[1])
                        widget_payload_raw = event[2]
                        break

                elapsed_out = round(time.time() - t0, 1)
                mode = "anthropic"

            elif adapt_mode == "openai_compat":
                # Real token streaming from the OpenAI-compatible provider.
                stream = llm.stream_openai_compat(
                    ctx["combined_prompt"], ctx["combined_system"],
                    timeout=combined_timeout, max_tokens=combined_max_tokens, temperature=0.2,
                )
                response_closed = False
                for event in parse_combined_stream(
                    stream,
                    emit_response_deltas=True,
                    emit_widget_deltas=True,
                ):
                    etype = event[0]
                    if etype == "response_delta":
                        yield sse_pack({"type": "response_delta", "delta": event[1]})
                    elif etype == "response_closed":
                        response_closed = True
                        response = strip_leaked_widget_json(event[1])
                    elif etype == "widget_start":
                        yield sse_pack({"type": "widget_start"})
                    elif etype == "widget_delta":
                        yield sse_pack({"type": "widget_delta", "delta": event[1]})
                    elif etype == "complete":
                        if not response_closed:
                            response = strip_leaked_widget_json(event[1])
                        widget_payload_raw = event[2]
                        break
                elapsed_out = round(time.time() - t0, 1)
                mode = "openai_compat"
            else:
                raise RuntimeError("Unsupported ADAPTIVE_LLM_MODE (expected openai_compat or anthropic)")

            # Finalize widget payload for the canonical 'done' event (JSON schema only).
            if widget_payload_raw:
                widget_schema, widget_html, widget_height, tag = _dispatch_json_mode_widget(widget_payload_raw)
                widget_debug = tag or ""
            if not response and not widget_payload_raw:
                response = "(No content)"

        except Exception as e:
            msg_err = str(e).strip() or repr(e)
            yield sse_pack({
                "type": "done",
                "format_rule": ctx["format_rule"],
                "elapsed": None,
                "llm_mode": mode,
                "response": "",
                "widget_html": "",
                "widget_schema": "",
                "widget_height": 0,
                "widget_debug": f"stream_error:{msg_err}",
                "error": msg_err,
            })
            return

        # Update in-memory history
        user = ctx["user"]
        user["history"].append({"user": msg, "assistant": response})
        user["history"] = user["history"][-20:]
        user["last_message"] = msg
        user["last_response"] = response
        user["msg_count"] += 1
        user["last_widget_present"] = bool(widget_html or widget_schema)

        yield sse_pack({
            "type": "done",
            "format_rule": ctx["format_rule"],
            "strategy": ctx.get("strat", ""),
            "ape": ctx.get("ape", {}),
            "elapsed": elapsed_out,
            "llm_mode": mode,
            "response": response,
            "widget_html": widget_html or "",
            "widget_schema": widget_schema or "",
            "widget_height": widget_height,
            "widget_debug": widget_debug,
        })

        # Persistence off the hot path
        bg.add_task(
            _persist_after_response,
            user_id=user_id, uid=uid, msg=msg, response=response,
            strategy=ctx.get("strat"), elapsed=elapsed_out,
            widget_present=bool(widget_html or widget_schema), pane="adaptive",
            widget_html=widget_html or "",
            widget_schema=widget_schema or "",
            widget_height=int(widget_height or 0),
        )

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Conversation clear / reset
# ---------------------------------------------------------------------------

@app.post("/api/rate")
def rate(req: RateReq, user_id: str = Depends(require_user_id)):
    """Thumbs on the LAST adaptive answer.

    Queued as an APE signal and sent on the user's NEXT /turn call — APE links
    it to its latest PENDING turn by (user, session) itself, so no turn id is
    needed here. An opposite thumb replaces a queued one (changed their mind).
    """
    direction = (req.direction or "").strip().lower()
    if direction not in ("up", "down"):
        return JSONResponse({"error": "direction must be 'up' or 'down'"}, status_code=400)
    user = engine.get_user(user_id)
    sig = "thumbs_up" if direction == "up" else "thumbs_down"
    other = "thumbs_down" if direction == "up" else "thumbs_up"
    q = user["pending_signals"]
    if other in q:
        q.remove(other)
    if sig not in q:
        q.append(sig)
    return {"ok": True, "queued": list(q)}


# ---------------------------------------------------------------------------
# APE playground (Home page live demo)
#
# Each visitor drives a SANDBOXED bandit user ("pg_<identity>") against the
# real APE engine — selections and rewards are genuine, but they never touch
# the visitor's actual chat learning. A thumb here both delivers the reward
# (APE attributes it to the latest PENDING playground turn) and triggers the
# next selection, so the scoreboard visibly evolves click by click.
# ---------------------------------------------------------------------------

PLAYGROUND_INTENTS = ["Decision", "Explanation", "Comparison", "Instructional", "Definitional", "Evaluation"]
_PLAYGROUND_SIGNALS = {"thumbs_up", "thumbs_down"}


class PlaygroundTurnReq(BaseModel):
    intent: str = "Comparison"
    signal: str | None = None  # thumbs_up | thumbs_down (rates the PREVIOUS pick)


@app.post("/api/playground/turn")
def playground_turn(req: PlaygroundTurnReq, user_id: str = Depends(require_user_id)):
    pg_user = f"pg_{user_id}"
    intent = req.intent if req.intent in PLAYGROUND_INTENTS else "Comparison"
    signals = [req.signal] if req.signal in _PLAYGROUND_SIGNALS else []
    res = ape_client.select_turn(pg_user, "playground", intent, signals)
    arms = ape_client.bandit_state(pg_user, intent=intent)
    # NOTE: the raw format directive (res["format_rule"]) is deliberately NOT
    # returned — those are engineered prompt strings and stay server-side.
    return {
        "ok": res["ok"],
        "reason": res["reason"],
        "strategy": res["strategy"],
        "selection_method": _public_method(res.get("selection_method")),
        "arms": _public_arms(arms),
    }


# The platform-overview aggregation scans a year of turns (~20s) — far too
# slow for a request path. A daemon thread computes it at startup and
# refreshes every 10 minutes; the endpoint only ever serves the cache.
_stats_cache: dict = {"ok": False, "warming": True}
_stats_lock = threading.Lock()


def _refresh_playground_stats() -> None:
    global _stats_cache
    ov = ape_client.platform_overview(days=365)
    if not ov:
        return  # keep the previous snapshot (or the warming placeholder)
    by_strategy = ov.get("by_strategy") or []
    default_row = next((s for s in by_strategy if s.get("strategy") == "standard_llm"), None)
    best = None
    for s in by_strategy:
        if s.get("strategy") == "standard_llm" or int(s.get("total_pulls", 0)) < 30:
            continue
        if best is None or float(s.get("avg_reward", 0)) > float(best.get("avg_reward", 0)):
            best = s
    snapshot = {
        "ok": True,
        "total_turns": int(ov.get("total_turns", 0)),
        "total_users": int(ov.get("total_active_users", 0)),
        "total_strategies": int(ov.get("total_strategies", 0)),
        "total_topics": int(ov.get("total_topics", 0)),
        "best_strategy": (best or {}).get("strategy"),
        "best_avg_reward": round(float((best or {}).get("avg_reward", 0.0)), 2),
        "default_avg_reward": round(float((default_row or {}).get("avg_reward", 0.0)), 2),
    }
    with _stats_lock:
        _stats_cache = snapshot


def _stats_refresher_loop() -> None:
    while True:
        try:
            _refresh_playground_stats()
        except Exception:
            pass
        time.sleep(600)


threading.Thread(target=_stats_refresher_loop, daemon=True).start()


@app.get("/api/playground/stats")
def playground_stats():
    with _stats_lock:
        return dict(_stats_cache)


@app.post("/api/conversation/clear")
def conversation_clear(user_id: str = Depends(require_user_id)):
    """Remove stored chat + widgets for this account."""
    persistence.delete_conversation_logs(user_id=user_id, pane="adaptive")
    engine.clear_conversation_thread(user_id)
    return {"ok": True}


@app.post("/api/reset")
def reset(req: ResetReq, user_id: str = Depends(require_user_id)):
    engine.reset_user(user_id)
    persistence.delete_conversation_logs(user_id=user_id, pane="adaptive")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Static assets + SPA fallback
# ---------------------------------------------------------------------------

_frontend_dist_assets_dir = config.INDEX_HTML.parent / "assets"
if _frontend_dist_assets_dir.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(_frontend_dist_assets_dir), html=False),
        name="frontend_assets",
    )


@app.get("/{full_path:path}", response_class=HTMLResponse)
def spa_fallback(full_path: str):
    # Never serve HTML for API URLs — return JSON 404 so client parsers don't break.
    if full_path.startswith("api"):
        return JSONResponse({"detail": "Not found"}, status_code=status.HTTP_404_NOT_FOUND)
    # Serve real files that live in the dist root (robots.txt, sitemap.xml,
    # favicon.svg, og.png, apple-touch-icon.png) before the SPA fallback so
    # crawlers and social unfurlers get the actual file, not the HTML shell.
    if full_path:
        dist = config.INDEX_HTML.parent.resolve()
        candidate = (dist / full_path).resolve()
        if candidate.is_file() and dist in candidate.parents:
            from fastapi.responses import FileResponse
            return FileResponse(str(candidate))
    if not config.INDEX_HTML.exists():
        return JSONResponse({
            "service": "APE backend", "status": "ok", "mode": "api-only",
            "note": "The web app is hosted separately; call the /api/* endpoints.",
        })
    html = config.INDEX_HTML.read_bytes()
    return HTMLResponse(content=html, media_type="text/html; charset=utf-8")


def run_server():
    """Run with uvicorn (production-ready)."""
    import uvicorn

    port = int(os.getenv("PORT", "5051"))
    print("=" * 60)
    print(f"  http://localhost:{port}   mode: {config.LLM_MODE}")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=port)
