"""PII-free structured JSON logs and per-stage latency summaries."""

from __future__ import annotations

import json
import logging
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator


class JsonFormatter(logging.Formatter):
    """Emit only explicitly supplied event fields; never serialize message payloads."""

    def format(self, record: logging.LogRecord) -> str:
        event = getattr(record, "event", record.getMessage())
        return json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname.lower(),
                "event": event,
                **getattr(record, "fields", {}),
            },
            separators=(",", ":"),
        )


class StageMetrics:
    """Thread-safe count and total latency per processing stage."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._totals: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])

    @contextmanager
    def measure(self, stage: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            with self._lock:
                values = self._totals[stage]
                values[0] += 1
                values[1] += elapsed_ms
            logging.getLogger(__name__).info(
                "stage_complete", extra={"event": "stage_complete", "fields": {"stage": stage, "latency_ms": round(elapsed_ms, 2)}}
            )

    def snapshot(self) -> dict[str, dict[str, float]]:
        with self._lock:
            return {
                name: {
                    "count": count,
                    "average_ms": round(total / count, 2) if count else 0,
                }
                for name, (count, total) in self._totals.items()
            }
