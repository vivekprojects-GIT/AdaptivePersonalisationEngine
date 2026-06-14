"""Retrieve relevant filings from ChromaDB and assemble the EVIDENCE PACKET
(the structured numbers + source_refs that belong to the retrieved documents)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import chromadb

# Strip presentation/chart phrasing before embedding for retrieval — "show me X as a
# stacked bar" should retrieve the same docs as "X". (The full query still drives the answer.)
_PRESENTATION_RE = re.compile(
    r"\b(as a|as an|in a|using a|show me|show|display|visuali[sz]e|plot|draw|give me|render|make me|make|create)\b"
    r"|\b(stacked|grouped|horizontal|vertical|line|bar|hbar|area|scatter|bubble|pie|donut|funnel|gauge|radar|combo|"
    r"heatmap|chart|charts|graph|graphs|diagram|dashboard|widget|visualization|visualisation)\b",
    re.IGNORECASE,
)


def _clean_for_retrieval(q: str) -> str:
    cleaned = re.sub(r"\s+", " ", _PRESENTATION_RE.sub(" ", q or "")).strip()
    return cleaned or q

DIR = Path(__file__).resolve().parent
DB_PATH = DIR / "chroma_db"
EVIDENCE_PATH = DIR / "evidence_index.json"
COLLECTION = "finance_filings"

# Distance gate for queries with NO known company named (catches off-topic like
# "weather", "compound interest"). Distance alone is unreliable when a metric is a
# minor mention (e.g. "gross margin"), so we ALSO use entity-aware gating below.
RELEVANCE_THRESHOLD = 0.78
ENTITY_THRESHOLD = 1.30  # looser cap fallback when a known company is named

# Companies actually in the corpus (name/alias/ticker → company_id). If a query names
# one of these, it's in-domain (let the synthesizer handle any missing metric); if it
# names a company NOT here (Netflix, Disney), it's refused.
_KNOWN: dict[str, str] = {
    "apple": "AAPL", "aapl": "AAPL",
    "microsoft": "MSFT", "msft": "MSFT",
    "alphabet": "GOOGL", "google": "GOOGL", "googl": "GOOGL",
    "amazon": "AMZN", "amzn": "AMZN",
    "nvidia": "NVDA", "nvda": "NVDA",
    "tesla": "TSLA", "tsla": "TSLA",
    "meta": "META", "facebook": "META",
}


def _mentioned_ids(q: str) -> set[str]:
    ql = (q or "").lower()
    return {cid for name, cid in _KNOWN.items() if re.search(r"\b" + re.escape(name) + r"\b", ql)}

_client = None
_col = None
_evidence: dict[str, dict] | None = None


def _load():
    global _client, _col, _evidence
    if _col is None:
        try:
            _client = chromadb.PersistentClient(path=str(DB_PATH))
            _col = _client.get_collection(COLLECTION)
        except Exception:
            _col = None  # collection missing/empty — app will refuse gracefully
    if _evidence is None:
        try:
            _evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        except Exception:
            _evidence = {}
    return _col, _evidence


def _empty(query: str) -> dict:
    return {"query": query, "doc_ids": [], "chunks": [], "metas": [],
            "evidence": [], "relevant": False, "best_distance": None}


def retrieve(query: str, k: int = 6) -> dict:
    col, evidence = _load()
    if col is None:
        return _empty(query)
    try:
        if col.count() == 0:
            return _empty(query)
    except Exception:
        pass
    # ENTITY-AWARE RETRIEVAL:
    # - Query NAMES companies we have → fetch ALL their docs (every fiscal year) by metadata,
    #   so multi-company comparisons get full coverage (embedding top-k can miss some).
    #   The synthesizer then picks the right year(s).
    # - Query names NO known company → embedding search + distance gate (catches off-topic).
    mentioned = _mentioned_ids(query)
    if mentioned:
        try:
            got = col.get(where={"company_id": {"$in": list(mentioned)}})
            gids = got.get("ids") or []
            gdocs = got.get("documents") or []
            gmetas = got.get("metadatas") or []
            kept = list(zip(gids, gdocs, gmetas, [0.0] * len(gids)))
        except Exception:
            kept = []
        if not kept:  # fallback: embedding pool filtered to mentioned companies
            res = col.query(query_texts=[_clean_for_retrieval(query)], n_results=24)
            rows = list(zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]))
            kept = [r for r in rows if r[2].get("company_id") in mentioned] or [
                r for r in rows if r[3] <= ENTITY_THRESHOLD
            ]
        kept = kept[:21]  # all docs for up to ~7 companies × 3 years
    else:
        res = col.query(query_texts=[_clean_for_retrieval(query)], n_results=max(k, 12))
        rows = list(zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]))
        kept = [r for r in rows if r[3] <= RELEVANCE_THRESHOLD][:9]
    relevant = len(kept) > 0

    doc_ids = [x[0] for x in kept]
    chunks = [x[1] for x in kept]
    kept_metas = [x[2] for x in kept]

    retrieved = set(doc_ids)
    packet = [rec for ref, rec in evidence.items() if ref.split("/", 1)[0] in retrieved]

    return {
        "query": query,
        "doc_ids": doc_ids,
        "chunks": chunks,
        "metas": kept_metas,
        "evidence": packet,
        "relevant": relevant,
        "best_distance": (min((x[3] for x in kept), default=None) if kept else None),
    }


def evidence_index() -> dict[str, dict]:
    _, evidence = _load()
    return evidence
