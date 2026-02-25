"""
local_buffer.py — Circular Buffer with JSON Persistence
Laptop Life-Saver System | Nyanza District

Stores up to BUFFER_MAX_SIZE records in memory (collections.deque) and
persists them to a JSON file so data survives agent restarts.
"""

import json
import logging
import os
from collections import deque
from typing import Optional

from .config import BUFFER_FILE, BUFFER_MAX_SIZE

logger = logging.getLogger(__name__)


class CircularBuffer:
    """Fixed-size circular buffer backed by a JSON file."""

    def __init__(self, maxlen: Optional[int] = None, filepath: Optional[str] = None):
        # Use config defaults if not specified
        self.maxlen = maxlen if maxlen is not None else BUFFER_MAX_SIZE
        self.filepath = filepath if filepath is not None else BUFFER_FILE
        
        self._buffer: deque = deque(maxlen=self.maxlen)
        self._load()

    # ── Public API ──────────────────────────────────────────────────

    def append(self, record: dict) -> None:
        """Add a record.  Oldest record is dropped if at capacity."""
        self._buffer.append(record)
        self._save()

    def flush(self) -> list[dict]:
        """Return all buffered records and clear the buffer."""
        records = list(self._buffer)
        self._buffer.clear()
        self._save()
        return records

    def peek(self) -> list[dict]:
        """Return all buffered records without clearing."""
        return list(self._buffer)

    def __len__(self) -> int:
        return len(self._buffer)

    def __iter__(self):
        return iter(self._buffer)

    def remove_first(self, n: int) -> None:
        """Remove the first n records from the buffer."""
        if n <= 0:
            return
        
        # Convert to list, slice, rebuild deque
        remaining = list(self._buffer)[n:]
        self._buffer.clear()
        for record in remaining:
            self._buffer.append(record)
        self._save()

    # ── Persistence ─────────────────────────────────────────────────

    def _load(self) -> None:
        """Load records from disk on startup."""
        if not os.path.exists(self.filepath):
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                # Only keep the most recent `maxlen` records
                recent: list[dict] = data[-self.maxlen :]
                for record in recent:
                    self._buffer.append(record)
                logger.info("Loaded %d records from buffer file", len(self._buffer))
        except (json.JSONDecodeError, IOError) as exc:
            logger.warning("Buffer file corrupt or unreadable: %s", exc)

    def _save(self) -> None:
        """Persist current buffer to disk."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as fh:
                json.dump(list(self._buffer), fh, default=str)
        except IOError as exc:
            logger.error("Failed to save buffer: %s", exc)
