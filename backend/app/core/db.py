"""SQLite persistence for sessions, interviews, task progress and scores."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager

from ..config import settings

_lock = threading.Lock()
_DB_PATH = settings.DATA_DIR / "placementpilot.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions   (id TEXT PRIMARY KEY, created REAL, data TEXT);
CREATE TABLE IF NOT EXISTS interviews (id TEXT PRIMARY KEY, session_id TEXT, created REAL, data TEXT);
CREATE TABLE IF NOT EXISTS task_state (session_id TEXT, task_id TEXT, done INTEGER, ts REAL,
                                       PRIMARY KEY (session_id, task_id));
CREATE TABLE IF NOT EXISTS scores     (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT,
                                       kind TEXT, ref TEXT, score REAL, meta TEXT, ts REAL);
"""


@contextmanager
def _conn():
    with _lock:
        c = sqlite3.connect(_DB_PATH, timeout=10)
        c.row_factory = sqlite3.Row
        try:
            c.executescript(SCHEMA)
            yield c
            c.commit()
        finally:
            c.close()


def new_id() -> str:
    return uuid.uuid4().hex[:12]


# ---- sessions -----------------------------------------------------------
def save_session(data: dict, session_id: str | None = None) -> str:
    sid = session_id or new_id()
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO sessions VALUES (?,?,?)", (sid, time.time(), json.dumps(data)))
    return sid


def get_session(sid: str) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT data FROM sessions WHERE id=?", (sid,)).fetchone()
    return json.loads(row["data"]) if row else None


def delete_session(sid: str) -> bool:
    with _conn() as c:
        n = c.execute("DELETE FROM sessions WHERE id=?", (sid,)).rowcount
        c.execute("DELETE FROM interviews WHERE session_id=?", (sid,))
        c.execute("DELETE FROM task_state WHERE session_id=?", (sid,))
        c.execute("DELETE FROM scores WHERE session_id=?", (sid,))
    return n > 0


# ---- interviews ---------------------------------------------------------
def save_interview(iid: str, session_id: str, data: dict) -> None:
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO interviews VALUES (?,?,?,?)", (iid, session_id, time.time(), json.dumps(data)))


def get_interview(iid: str) -> tuple[str, dict] | None:
    with _conn() as c:
        row = c.execute("SELECT session_id, data FROM interviews WHERE id=?", (iid,)).fetchone()
    return (row["session_id"], json.loads(row["data"])) if row else None


def list_interviews(session_id: str) -> list[dict]:
    with _conn() as c:
        rows = c.execute("SELECT id, data FROM interviews WHERE session_id=? ORDER BY created", (session_id,)).fetchall()
    return [{"id": r["id"], **json.loads(r["data"])} for r in rows]


# ---- tasks & scores -----------------------------------------------------
def set_task(session_id: str, task_id: str, done: bool) -> None:
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO task_state VALUES (?,?,?,?)", (session_id, task_id, int(done), time.time()))


def get_task_state(session_id: str) -> dict[str, bool]:
    with _conn() as c:
        rows = c.execute("SELECT task_id, done FROM task_state WHERE session_id=?", (session_id,)).fetchall()
    return {r["task_id"]: bool(r["done"]) for r in rows}


def add_score(session_id: str, kind: str, ref: str, score: float, meta: dict | None = None) -> None:
    with _conn() as c:
        c.execute("INSERT INTO scores (session_id, kind, ref, score, meta, ts) VALUES (?,?,?,?,?,?)",
                  (session_id, kind, ref, float(score), json.dumps(meta or {}), time.time()))


def get_scores(session_id: str, kind: str | None = None) -> list[dict]:
    q, args = "SELECT kind, ref, score, meta, ts FROM scores WHERE session_id=?", [session_id]
    if kind:
        q += " AND kind=?"
        args.append(kind)
    with _conn() as c:
        rows = c.execute(q + " ORDER BY ts", args).fetchall()
    return [{"kind": r["kind"], "ref": r["ref"], "score": r["score"], "meta": json.loads(r["meta"]), "ts": r["ts"]} for r in rows]
