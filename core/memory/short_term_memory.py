"""
Short-Term Memory (STM)

Purpose:
- Store recent conversational continuity
- Limited size
- Fast recall
- Automatic decay (TTL)
- Safe, filtered read access
"""

import time
from collections import deque
from typing import Iterable


class ShortTermMemory:
    # ===============================
    # DAY 21.3 — STM LIMITS (LOCKED)
    # ===============================
    MAX_ITEMS = 50          # hard cap
    TTL_SECONDS = 300       # 5 minutes

    # ===============================
    # DAY 21.4 — READ SAFETY LIMITS
    # ===============================
    MAX_READ_LIMIT = 10     # absolute cap for reads
    DEFAULT_READ_LIMIT = 5
    MIN_READ_CONFIDENCE = 0.70

    def __init__(self):
        # deque preserves insertion order (FIFO)
        self._items = deque()

    # -------------------------------
    # Internal helpers
    # -------------------------------
    def _now(self) -> float:
        return time.time()

    def _cleanup(self):
        """
        Remove expired or excess entries.
        """
        now = self._now()

        # TTL-based eviction
        while self._items and (now - self._items[0]["timestamp"] > self.TTL_SECONDS):
            self._items.popleft()

        # Capacity-based eviction (FIFO)
        while len(self._items) > self.MAX_ITEMS:
            self._items.popleft()

    # -------------------------------
    # Public API — WRITE
    # -------------------------------
    def store(self, *, role: str, content: str, intent: str, confidence: float):
        """
        Store a short-term memory entry (in-memory only).
        """
        self._items.append({
            "role": role,
            "content": content,
            "intent": intent,
            "confidence": confidence,
            "timestamp": self._now(),
        })

        # Enforce limits immediately
        self._cleanup()

    # -------------------------------
    # Public API — READ (SAFE)
    # -------------------------------
    def fetch_recent(
        self,
        *,
        limit: int | None = None,
        role: str | None = None,
        intents: Iterable[str] | None = None,
        min_confidence: float | None = None,
    ):
        """
        Fetch recent STM entries with strict safety rules.

        Rules:
        - Hard cap on returned items
        - Optional role filter ("user" / "assistant")
        - Optional intent filter
        - Confidence floor enforced
        - Newest-last ordering
        """

        self._cleanup()

        # ---------------------------
        # Resolve and validate limits
        # ---------------------------
        if limit is None:
            limit = self.DEFAULT_READ_LIMIT

        if limit <= 0 or limit > self.MAX_READ_LIMIT:
            return []

        if min_confidence is None:
            min_confidence = self.MIN_READ_CONFIDENCE

        # ---------------------------
        # Start with all items
        # ---------------------------
        items = list(self._items)

        # ---------------------------
        # Role filter
        # ---------------------------
        if role is not None:
            if role not in {"user", "assistant"}:
                return []
            items = [x for x in items if x["role"] == role]

        # ---------------------------
        # Intent filter
        # ---------------------------
        if intents is not None:
            intents = set(intents)
            items = [x for x in items if x["intent"] in intents]

        # ---------------------------
        # Confidence filter
        # ---------------------------
        items = [x for x in items if x["confidence"] >= min_confidence]

        # ---------------------------
        # Return newest-last slice
        # ---------------------------
        return items[-limit:]

    def clear(self):
        """
        Clear all STM entries.
        """
        self._items.clear()
