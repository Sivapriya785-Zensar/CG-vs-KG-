"""
Persistent decision-trace store (SQLite -- local file, no external service,
no credentials). Traces survive across sessions: a fact stored in session A
is retrievable when answering a question in session B -- *for the same
user*. A session is one conversation; a user can have many sessions over
time, and traces are scoped to `user_id`, not `session_id`, precisely so
that unrelated users/customers never see each other's stored facts. (An
earlier version of this store had no user_id at all and pooled every
session's traces globally -- harmless with one interactive user, but it
silently cross-contaminated the 50-question test suite: by the time later
test cases ran, the store already held several different customers'
conflicting loyalty-tier statements, which the fail-safe conflict check
correctly treated as ambiguous and fell back on. That was a test-harness
bug, not a finding about the mechanism -- see README.md.)

Also hosts the opt-in answer cache (see agent/cache.py for the policy around
when it's used -- this module only provides the storage primitives).
"""
import json
import math
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from kg_cg_experiment.config import TRACE_DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    entity_key TEXT NOT NULL,
    attribute TEXT NOT NULL,
    value TEXT NOT NULL,
    raw_statement TEXT NOT NULL,
    session_id TEXT NOT NULL,
    kg_node_id TEXT,
    embedding TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS answer_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    question_text TEXT NOT NULL,
    kg_context_hash TEXT NOT NULL,
    trace_fingerprint TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    embedding TEXT NOT NULL,
    created_at REAL NOT NULL
);
"""


@dataclass
class TraceRow:
    id: int
    user_id: str
    entity_key: str
    attribute: str
    value: str
    raw_statement: str
    session_id: str
    kg_node_id: str | None
    created_at: float

    @property
    def slot(self) -> tuple[str, str]:
        return (self.entity_key, self.attribute)


@dataclass
class CacheRow:
    id: int
    question_text: str
    kg_context_hash: str
    trace_fingerprint: str
    answer_text: str
    prompt_tokens: int
    completion_tokens: int
    created_at: float


def _ensure_dir():
    Path(TRACE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def _conn():
    _ensure_dir()
    conn = sqlite3.connect(TRACE_DB_PATH)
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


_TRACE_COLUMNS = "id, user_id, entity_key, attribute, value, raw_statement, session_id, kg_node_id, embedding, created_at"


def _row_to_trace(row) -> TraceRow:
    return TraceRow(
        id=row[0], user_id=row[1], entity_key=row[2], attribute=row[3], value=row[4],
        raw_statement=row[5], session_id=row[6], kg_node_id=row[7], created_at=row[9],
    )


def add_trace(user_id: str, entity_key: str, attribute: str, value: str, raw_statement: str,
              session_id: str, embedding: list[float], kg_node_id: str | None = None) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO traces (user_id, entity_key, attribute, value, raw_statement, session_id, "
            "kg_node_id, embedding, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (user_id, entity_key, attribute, value, raw_statement, session_id, kg_node_id,
             json.dumps(embedding), time.time()),
        )
        return cur.lastrowid


def all_traces() -> list[TraceRow]:
    with _conn() as conn:
        rows = conn.execute(f"SELECT {_TRACE_COLUMNS} FROM traces ORDER BY created_at DESC").fetchall()
        return [_row_to_trace(r) for r in rows]


def traces_by_slot(user_id: str, entity_key: str, attribute: str) -> list[TraceRow]:
    with _conn() as conn:
        rows = conn.execute(
            f"SELECT {_TRACE_COLUMNS} FROM traces WHERE user_id=? AND entity_key=? AND attribute=? "
            "ORDER BY created_at DESC",
            (user_id, entity_key, attribute),
        ).fetchall()
        return [_row_to_trace(r) for r in rows]


def traces_by_session(session_id: str) -> list[TraceRow]:
    with _conn() as conn:
        rows = conn.execute(
            f"SELECT {_TRACE_COLUMNS} FROM traces WHERE session_id=? ORDER BY created_at DESC",
            (session_id,),
        ).fetchall()
        return [_row_to_trace(r) for r in rows]


def search_similar(user_id: str, query_embedding: list[float], threshold: float, top_k: int = 10) -> list[tuple[TraceRow, float]]:
    """Direct embedding recall, scoped to this user: compare the query
    embedding against every trace *this user* has on record. Real cosine
    similarity, computed fresh every call -- no caching of results, no
    shortcuts."""
    with _conn() as conn:
        rows = conn.execute(f"SELECT {_TRACE_COLUMNS} FROM traces WHERE user_id=?", (user_id,)).fetchall()

    scored = []
    for row in rows:
        trace_embedding = json.loads(row[8])
        score = _cosine(query_embedding, trace_embedding)
        if score >= threshold:
            scored.append((_row_to_trace(row), score))
    scored.sort(key=lambda t: -t[1])
    return scored[:top_k]


def clear_all():
    """Wipes the trace store. Only for test-suite isolation, never called
    from the interactive UI."""
    with _conn() as conn:
        conn.execute("DELETE FROM traces")
        conn.execute("DELETE FROM answer_cache")


# ---- answer cache (opt-in reuse, see agent/cache.py for policy) ----

def cache_add(user_id: str, question_text: str, kg_context_hash: str, trace_fingerprint: str,
              answer_text: str, prompt_tokens: int, completion_tokens: int,
              embedding: list[float]) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO answer_cache (user_id, question_text, kg_context_hash, trace_fingerprint, "
            "answer_text, prompt_tokens, completion_tokens, embedding, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (user_id, question_text, kg_context_hash, trace_fingerprint, answer_text,
             prompt_tokens, completion_tokens, json.dumps(embedding), time.time()),
        )
        return cur.lastrowid


def cache_search(user_id: str, query_embedding: list[float], kg_context_hash: str, trace_fingerprint: str,
                  threshold: float) -> CacheRow | None:
    """Only returns a hit if the paraphrase similarity clears `threshold`
    AND both the KG context and the exact set of trace values used are
    byte-identical to what was cached -- a close-enough question with
    different underlying evidence must not reuse a stale answer. Scoped to
    this user so one customer's cached answer never serves another's."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, question_text, kg_context_hash, trace_fingerprint, answer_text, "
            "prompt_tokens, completion_tokens, embedding, created_at FROM answer_cache "
            "WHERE user_id=? AND kg_context_hash=? AND trace_fingerprint=?",
            (user_id, kg_context_hash, trace_fingerprint),
        ).fetchall()

    best = None
    best_score = -1.0
    for row in rows:
        score = _cosine(query_embedding, json.loads(row[7]))
        if score >= threshold and score > best_score:
            best_score = score
            best = row
    if best is None:
        return None
    return CacheRow(
        id=best[0], question_text=best[1], kg_context_hash=best[2],
        trace_fingerprint=best[3], answer_text=best[4],
        prompt_tokens=best[5], completion_tokens=best[6], created_at=best[8],
    )
