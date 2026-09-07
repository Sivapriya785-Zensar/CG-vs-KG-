"""In-memory session store: per-session conversation turns for Condition B."""
import threading

_lock = threading.Lock()
_SESSIONS: dict[str, list[dict]] = {}


def get_turns(session_id: str) -> list[dict]:
    with _lock:
        return list(_SESSIONS.get(session_id, []))


def append_turn(session_id: str, role: str, content: str) -> None:
    with _lock:
        _SESSIONS.setdefault(session_id, []).append({"role": role, "content": content})


def seed_turns(session_id: str, turns: list[dict]) -> None:
    with _lock:
        _SESSIONS[session_id] = list(turns)


def reset(session_id: str) -> None:
    with _lock:
        _SESSIONS.pop(session_id, None)
