from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Dict, List

from sqlalchemy import Column, Integer, LargeBinary, String, Text, create_engine, select, text
from sqlalchemy.orm import declarative_base, sessionmaker

from . import config

Base = declarative_base()


class UserRow(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(LargeBinary, nullable=False)


class ConversationLogRow(Base):
    __tablename__ = "conversation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    pane = Column(String, nullable=False)  # "adaptive" | "baseline"
    role = Column(String, nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)

    strategy = Column(String, nullable=True)
    elapsed = Column(String, nullable=True)
    widget = Column(Integer, nullable=False, default=0)
    ts = Column(Integer, nullable=False, default=0)
    # Persisted widget payload so SPA reload can restore interactive widgets.
    widget_html = Column(Text, nullable=False, default="")
    widget_schema = Column(Text, nullable=False, default="")
    widget_height = Column(Integer, nullable=False, default=0)


class UserPrimitiveRow(Base):
    __tablename__ = "user_primitives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    instruction = Column(Text, nullable=False)
    created_ts = Column(Integer, nullable=False, default=0)
    updated_ts = Column(Integer, nullable=False, default=0)


_PRIMITIVES_LOCK = threading.Lock()


def _read_primitives_json() -> dict:
    """
    primitives.json format:
      {
        "<user_id>": {
          "next_id": 1,
          "items": [{ id, name, instruction, created_ts, updated_ts }, ...]
        }
      }
    """
    path = getattr(config, "PRIMITIVES_JSON_PATH", str(config.HERE.parent / "data" / "user_primitives.json"))
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _atomic_write_primitives_json(data: dict) -> None:
    path = getattr(config, "PRIMITIVES_JSON_PATH", str(config.HERE.parent / "data" / "user_primitives.json"))
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


_engine = None
_SessionLocal = None


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _json_loads(s: str | None, default: Any) -> Any:
    if not s:
        return default
    return json.loads(s)


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(
            f"sqlite:///{config.DB_PATH}",
            connect_args={"check_same_thread": False},
        )
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def init_db() -> None:
    eng = get_engine()
    Base.metadata.create_all(bind=eng)
    _migrate_conversation_log_widget_columns()


def _migrate_conversation_log_widget_columns() -> None:
    """SQLite: add widget payload columns to existing DBs (create_all does not ALTER)."""
    eng = get_engine()
    with eng.connect() as conn:
        rows = conn.execute(text("PRAGMA table_info(conversation_logs)")).fetchall()
        colnames = {str(r[1]) for r in rows}
        stmts: list[str] = []
        if "widget_html" not in colnames:
            stmts.append(
                "ALTER TABLE conversation_logs ADD COLUMN widget_html TEXT NOT NULL DEFAULT ''"
            )
        if "widget_schema" not in colnames:
            stmts.append(
                "ALTER TABLE conversation_logs ADD COLUMN widget_schema TEXT NOT NULL DEFAULT ''"
            )
        if "widget_height" not in colnames:
            stmts.append(
                "ALTER TABLE conversation_logs ADD COLUMN widget_height INTEGER NOT NULL DEFAULT 0"
            )
        for s in stmts:
            conn.execute(text(s))
        if stmts:
            conn.commit()


def log_conversation_message(
    *,
    user_id: str,
    pane: str,
    role: str,
    content: str,
    strategy: str | None = None,
    elapsed: float | None = None,
    widget: bool = False,
    widget_html: str = "",
    widget_schema: str = "",
    widget_height: int = 0,
    ts: int | None = None,
) -> None:
    Session = _SessionLocal
    assert Session is not None
    now = int(ts if ts is not None else time.time())
    with Session() as session:
        session.add(
            ConversationLogRow(
                user_id=user_id,
                pane=str(pane),
                role=str(role),
                content=str(content or ""),
                strategy=str(strategy) if strategy else None,
                elapsed=str(elapsed) if elapsed is not None else None,
                widget=1 if widget else 0,
                ts=now,
                widget_html=str(widget_html or ""),
                widget_schema=str(widget_schema or ""),
                widget_height=int(widget_height or 0),
            )
        )
        session.commit()


def get_recent_conversation_messages(*, user_id: str, pane: str, limit: int = 80) -> List[Dict[str, Any]]:
    Session = _SessionLocal
    assert Session is not None
    lim = max(1, min(int(limit), 400))
    with Session() as session:
        rows = (
            session.execute(
                select(ConversationLogRow)
                .where(ConversationLogRow.user_id == user_id)
                .where(ConversationLogRow.pane == pane)
                .order_by(ConversationLogRow.id.desc())
                .limit(lim)
            )
            .scalars()
            .all()
        )
        rows = list(reversed(rows))
        return [
            {
                "role": r.role,
                "content": r.content,
                "strategy": r.strategy,
                "elapsed": r.elapsed,
                "widget": bool(r.widget),
                "ts": r.ts,
                "widget_html": getattr(r, "widget_html", None) or "",
                "widget_schema": getattr(r, "widget_schema", None) or "",
                "widget_height": int(getattr(r, "widget_height", None) or 0),
            }
            for r in rows
        ]


def delete_conversation_logs(*, user_id: str, pane: str | None = None) -> None:
    Session = _SessionLocal
    assert Session is not None
    with Session() as session:
        q = ConversationLogRow.__table__.delete().where(ConversationLogRow.user_id == user_id)  # type: ignore[attr-defined]
        if pane:
            q = q.where(ConversationLogRow.pane == pane)
        session.execute(q)
        session.commit()


def list_user_primitives(user_id: str) -> List[Dict[str, Any]]:
    with _PRIMITIVES_LOCK:
        data = _read_primitives_json()
        box = data.get(user_id) or {}
        items = box.get("items") if isinstance(box, dict) else None
        if not isinstance(items, list):
            return []
        out: List[Dict[str, Any]] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            prim_id = int(it.get("id") or 0)
            name = str(it.get("name") or "")
            inst = str(it.get("instruction") or "")
            if prim_id <= 0 or not name or not inst:
                continue
            out.append(
                {
                    "id": prim_id,
                    "name": name,
                    "instruction": inst,
                    "created_ts": int(it.get("created_ts") or 0),
                    "updated_ts": int(it.get("updated_ts") or 0),
                }
            )
        out.sort(key=lambda x: x["id"])
        # Migration fallback:
        # If the user has primitives in the legacy SQLite table, but JSON is empty,
        # automatically copy them into JSON so the UI can show everything.
        if out:
            return out

        try:
            Session = _SessionLocal
            if Session is None:
                # Ensure engine/session exists (init_db should have done this).
                get_engine()
                Session = _SessionLocal
            assert Session is not None
            with Session() as session:
                rows = (
                    session.execute(
                        select(UserPrimitiveRow)
                        .where(UserPrimitiveRow.user_id == user_id)
                        .order_by(UserPrimitiveRow.id.asc())
                    )
                    .scalars()
                    .all()
                )
                if not rows:
                    return []
                migrated: List[Dict[str, Any]] = []
                max_id = 0
                for r in rows:
                    prim_id = int(getattr(r, "id") or 0)
                    if prim_id <= 0:
                        continue
                    max_id = max(max_id, prim_id)
                    migrated.append(
                        {
                            "id": prim_id,
                            "name": str(getattr(r, "name") or ""),
                            "instruction": str(getattr(r, "instruction") or ""),
                            "created_ts": int(getattr(r, "created_ts") or 0),
                            "updated_ts": int(getattr(r, "updated_ts") or 0),
                        }
                    )

                if not migrated:
                    return []

                # Write into JSON.
                data = _read_primitives_json()
                data[user_id] = {"next_id": max_id + 1, "items": migrated}
                _atomic_write_primitives_json(data)
                return migrated
        except Exception:
            # If migration fails for any reason, return the JSON (empty) result.
            return []


def create_user_primitive(*, user_id: str, name: str, instruction: str) -> Dict[str, Any]:
    now = int(time.time())
    nm = str(name).strip()
    inst = str(instruction).strip()

    with _PRIMITIVES_LOCK:
        data = _read_primitives_json()
        box = data.get(user_id) or {"next_id": 1, "items": []}
        if not isinstance(box, dict):
            box = {"next_id": 1, "items": []}
        items = box.get("items") or []
        if not isinstance(items, list):
            items = []

        next_id = int(box.get("next_id") or 1)
        if items:
            max_id = max([int(it.get("id") or 0) for it in items if isinstance(it, dict)], default=0)
            next_id = max(next_id, max_id + 1)

        new_item = {"id": next_id, "name": nm, "instruction": inst, "created_ts": now, "updated_ts": now}
        items.append(new_item)
        box["items"] = items
        box["next_id"] = next_id + 1
        data[user_id] = box
        _atomic_write_primitives_json(data)
        return new_item


def update_user_primitive(*, user_id: str, prim_id: int, name: str, instruction: str) -> Dict[str, Any] | None:
    now = int(time.time())
    nm = str(name).strip()
    inst = str(instruction).strip()
    with _PRIMITIVES_LOCK:
        data = _read_primitives_json()
        box = data.get(user_id) or {}
        if not isinstance(box, dict):
            return None
        items = box.get("items") or []
        if not isinstance(items, list):
            return None

        found = False
        created_ts = 0
        for it in items:
            if not isinstance(it, dict):
                continue
            if int(it.get("id") or 0) != int(prim_id):
                continue
            it["name"] = nm
            it["instruction"] = inst
            it["updated_ts"] = now
            created_ts = int(it.get("created_ts") or 0)
            found = True
            break

        if not found:
            return None

        box["items"] = items
        data[user_id] = box
        _atomic_write_primitives_json(data)
        return {"id": int(prim_id), "name": nm, "instruction": inst, "created_ts": created_ts, "updated_ts": now}


def delete_user_primitive(*, user_id: str, prim_id: int) -> bool:
    with _PRIMITIVES_LOCK:
        data = _read_primitives_json()
        box = data.get(user_id)
        if not isinstance(box, dict):
            return False
        items = box.get("items") or []
        if not isinstance(items, list):
            return False
        before = len(items)
        items = [it for it in items if not (isinstance(it, dict) and int(it.get("id") or 0) == int(prim_id))]
        if len(items) == before:
            return False
        box["items"] = items
        data[user_id] = box
        _atomic_write_primitives_json(data)
        return True


def load_users_from_db() -> List[Dict[str, Any]]:
    Session = _SessionLocal
    assert Session is not None
    with Session() as session:
        rows = session.execute(select(UserRow)).scalars().all()
        return [
            {
                "user_id": r.user_id,
                "username": r.username,
                "email": r.email,
                "password_hash": r.password_hash,
            }
            for r in rows
        ]


def persist_user(user_rec: Any) -> None:
    """
    Upsert a user record into `users`.
    `user_rec` can be `backend.auth.UserRecord` or any object with
    {user_id, username, email, password_hash}.
    """
    Session = _SessionLocal
    assert Session is not None

    with Session() as session:
        existing = session.execute(select(UserRow).where(UserRow.user_id == user_rec.user_id)).scalar_one_or_none()
        if existing is None:
            session.add(
                UserRow(
                    user_id=user_rec.user_id,
                    username=user_rec.username,
                    email=user_rec.email,
                    password_hash=user_rec.password_hash,
                )
            )
        else:
            existing.username = user_rec.username
            existing.email = user_rec.email
            existing.password_hash = user_rec.password_hash
        session.commit()




