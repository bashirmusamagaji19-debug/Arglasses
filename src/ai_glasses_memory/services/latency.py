from __future__ import annotations

from time import perf_counter


class LatencyTracker:
    """记录 pipeline 各阶段的毫秒级耗时。"""

    def __init__(self) -> None:
        self._started_at = perf_counter()
        self._stage_started_at = self._started_at
        self._latency_ms: dict[str, float] = {}

    def mark(self, stage: str) -> None:
        now = perf_counter()
        self._latency_ms[stage] = round((now - self._stage_started_at) * 1000, 3)
        self._stage_started_at = now

    def finish(self) -> dict[str, float]:
        self._latency_ms["total"] = round((perf_counter() - self._started_at) * 1000, 3)
        return dict(self._latency_ms)
