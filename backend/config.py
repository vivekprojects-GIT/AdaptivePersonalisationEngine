"""Configuration and constants for the Adaptive Presentation Engine backend.

Loads environment variables from .env (via python-dotenv) and defines runtime
configuration: LLM provider selection, API keys, paths.
Restart the server after changing .env.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env into os.environ; override=True lets existing env vars win (Docker/CI).
load_dotenv(override=True)

# Some environments (e.g. Claude Code / Anthropic CLI tooling) export an EMPTY
# ANTHROPIC_AUTH_TOKEN (and similar). The Anthropic SDK then prefers bearer auth and
# emits an invalid "Authorization: Bearer " header with no token, which httpx rejects
# and the SDK reports as APIConnectionError ("Connection error") on every call. Drop
# blank values so the SDK falls back to ANTHROPIC_API_KEY (x-api-key).
for _blank_var in ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_CUSTOM_HEADERS"):
    if not (os.environ.get(_blank_var) or "").strip():
        os.environ.pop(_blank_var, None)

# -----------------------------------------------------------------------------
# LLM provider and endpoint routing
# -----------------------------------------------------------------------------
# Primary mode: "anthropic" (Claude) or "openai_compat" (OpenAI/Groq).
LLM_MODE = os.getenv("LLM_MODE", "anthropic").lower()

# Per-endpoint override: /api/chat -> ADAPTIVE. (Baseline lane removed in v2.)
ADAPTIVE_LLM_MODE = os.getenv("ADAPTIVE_LLM_MODE", LLM_MODE).lower()

# Widget output: "html" (full HTML in iframe) or "json" (UI schema for frontend renderer).
WIDGET_MODE = os.getenv("WIDGET_MODE", "json").strip().lower()


def _flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")

# Feature flags (default OFF):
# - USE_RAG: when off, no ChromaDB retrieval; the model fills figures from its own knowledge.
USE_RAG = _flag("USE_RAG", "0")

# Max time (sec) and tokens for combined response+widget generation.
# Tight defaults so latency stays predictable; raise only when the UI shows truncation.
COMBINED_TIMEOUT_SECONDS = int(os.getenv("COMBINED_TIMEOUT_SECONDS", "45"))
COMBINED_MAX_TOKENS = int(os.getenv("COMBINED_MAX_TOKENS", "6000"))

# OpenAI-compatible API (Groq, OpenAI, or any chat/completions provider)
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "llama-3.1-8b-instant")

# Anthropic Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6")

# Anthropic Fast Mode: beta header for faster inference; we retry on failure.
ANTHROPIC_FAST_MODE_ENABLED = os.getenv("ANTHROPIC_FAST_MODE_ENABLED", "1").strip().lower() in {
    "1", "true", "yes", "on"
}
ANTHROPIC_FAST_MODE_SPEED = os.getenv("ANTHROPIC_FAST_MODE_SPEED", "fast")  # "fast" or "standard"
ANTHROPIC_FAST_MODE_BETA = os.getenv("ANTHROPIC_FAST_MODE_BETA", "fast-mode-2026-02-01")

# Opus 4.8 reasoning effort: "high" | "medium" | "low" (blank = omit / model default).
ANTHROPIC_EFFORT = os.getenv("ANTHROPIC_EFFORT", "").strip().lower()

# Some newer models (e.g. opus-4-8) deprecate/reject the `temperature` param.
# "auto" omits it for those models; "1"/"0" force on/off.
ANTHROPIC_SEND_TEMPERATURE = os.getenv("ANTHROPIC_SEND_TEMPERATURE", "auto").strip().lower()

# Internal marker placed between the stable (cacheable) prefix and the per-turn
# tail of the combined system prompt. The Anthropic path splits on it to apply
# prompt caching to the prefix; other paths strip it. Never sent to the model.
SYSTEM_CACHE_BOUNDARY = "<<<__CACHE_BOUNDARY__>>>"
# Prompt caching on the stable system prefix (90% cheaper input on cache hits).
ANTHROPIC_PROMPT_CACHE = _flag("ANTHROPIC_PROMPT_CACHE", "1")

# Paths: HERE = backend/, parent = vivek/ (project root).
HERE = Path(__file__).resolve().parent
# Frontend entry point served at GET / — the Vite production build.
INDEX_HTML = HERE.parent / "frontend" / "dist" / "index.html"

# Skills document — high-level chart/widget guidance injected into LLM prompts.
# Override with SKILLS_PATH env var if needed.
SKILLS_PATH = Path(os.getenv("SKILLS_PATH", str(HERE.parent / "data" / "skills.md")))
SKILLS_CONTENT = SKILLS_PATH.read_text(encoding="utf-8") if SKILLS_PATH.exists() else ""

# -----------------------------------------------------------------------------
# Auth (JWT)
# -----------------------------------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "dev-change-me-please")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_SECONDS = int(os.getenv("JWT_EXPIRE_SECONDS", str(60 * 60 * 24 * 7)))

# -----------------------------------------------------------------------------
# Google Sign-In (optional)
# -----------------------------------------------------------------------------
# OAuth 2.0 Web client ID from Google Cloud Console. When empty, the Google
# login button is hidden and /api/auth/google returns 503. The SAME value must
# be exposed to the frontend build as VITE_GOOGLE_CLIENT_ID.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()

# -----------------------------------------------------------------------------
# Admin authorization (primitives are admin-only)
# -----------------------------------------------------------------------------
# Admins can manage primitives and have their primitives injected into the LLM prompt.
#
# Setup options:
# 1) Provide a single admin to auto-create on startup:
#    - ADMIN_USERNAME
#    - ADMIN_EMAIL
#    - ADMIN_PASSWORD
# 2) Or mark existing users as admin via lists:
#    - ADMIN_USERNAMES (comma-separated)
#    - ADMIN_EMAILS (comma-separated)
# 3) Or mark specific users by id:
#    - ADMIN_USER_IDS (comma-separated)
#
# If no admin config is provided, the backend keeps the previous behavior
# (any authenticated user can access primitives).
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip()
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()

def _split_csv(s: str) -> list[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]

ADMIN_USERNAMES = _split_csv(os.getenv("ADMIN_USERNAMES", "")) or ([ADMIN_USERNAME] if ADMIN_USERNAME else [])
ADMIN_EMAILS = _split_csv(os.getenv("ADMIN_EMAILS", "")) or ([ADMIN_EMAIL] if ADMIN_EMAIL else [])
ADMIN_USER_IDS = _split_csv(os.getenv("ADMIN_USER_IDS", ""))

# Used by server-side gating logic.
ADMIN_CONFIGURED = bool(ADMIN_USERNAMES or ADMIN_EMAILS or ADMIN_USER_IDS)

# SQLite persistence
DB_PATH = os.getenv("DB_PATH", str(HERE.parent / "adaptiveui.sqlite3"))

# JSON persistence for user primitives (when DB/SQL is not desired).
PRIMITIVES_JSON_PATH = os.getenv("PRIMITIVES_JSON_PATH", str(HERE.parent / "data" / "user_primitives.json"))
