"""In-memory session store for per-session conversation history.

Each session holds an ordered list of {role, content} dicts compatible
with the Gemini multi-turn content format.  Sessions are capped at
MAX_TURNS message-pairs to keep context windows manageable.
"""

import threading
import time
from collections import deque
from typing import Optional

# Maximum number of individual messages kept per session (user + model)
MAX_MESSAGES = 40
# Sessions inactive for longer than this are evicted (seconds)
SESSION_TTL = 60 * 60 * 2  # 2 hours


class SessionStore:
    """Thread-safe, TTL-based in-memory conversation store."""

    def __init__(self, max_messages: int = MAX_MESSAGES, ttl: int = SESSION_TTL):
        self._sessions: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._max_messages = max_messages
        self._ttl = ttl

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_history(self, session_id: str) -> list[dict]:
        """Return conversation history for a session (empty list if new)."""
        with self._lock:
            self._evict_expired()
            session = self._sessions.get(session_id)
            if session is None:
                return []
            session["last_access"] = time.monotonic()
            return list(session["messages"])

    def append(self, session_id: str, role: str, content: str) -> None:
        """Append a single message to the session history."""
        with self._lock:
            self._evict_expired()
            if session_id not in self._sessions:
                self._sessions[session_id] = {
                    "messages": deque(maxlen=self._max_messages),
                    "last_access": time.monotonic(),
                    "created_at": time.monotonic(),
                }
            session = self._sessions[session_id]
            session["messages"].append({"role": role, "content": content})
            session["last_access"] = time.monotonic()

    def clear(self, session_id: str) -> bool:
        """Delete a session. Returns True if it existed."""
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def session_exists(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._sessions

    def message_count(self, session_id: str) -> int:
        with self._lock:
            session = self._sessions.get(session_id)
            return len(session["messages"]) if session else 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evict_expired(self) -> None:
        """Remove sessions that have been idle past TTL (call while holding lock)."""
        now = time.monotonic()
        expired = [
            sid
            for sid, data in self._sessions.items()
            if now - data["last_access"] > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_store: Optional[SessionStore] = None
_store_lock = threading.Lock()


def get_session_store() -> SessionStore:
    """Get or create the global SessionStore singleton."""
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = SessionStore()
    return _store
