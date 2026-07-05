"""Prometheus-compatible metrics for task monitoring."""

from __future__ import annotations

import time
from typing import Any


class Counter:
    """Simple counter metric."""

    def __init__(self, name: str, description: str, labels: list[str] | None = None) -> None:
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: dict[tuple[str, ...], float] = {}

    def inc(self, amount: float = 1.0, **label_values: str) -> None:
        key = tuple(label_values.get(l, "") for l in self.labels)
        self._values[key] = self._values.get(key, 0.0) + amount

    def get(self, **label_values: str) -> float:
        key = tuple(label_values.get(l, "") for l in self.labels)
        return self._values.get(key, 0.0)


class Histogram:
    """Simple histogram metric for tracking distributions."""

    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)

    def __init__(self, name: str, description: str, buckets: tuple[float, ...] | None = None) -> None:
        self.name = name
        self.description = description
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._observations: list[float] = []

    def observe(self, value: float) -> None:
        self._observations.append(value)

    @property
    def count(self) -> int:
        return len(self._observations)

    @property
    def sum(self) -> float:
        return sum(self._observations)

    def get_bucket_counts(self) -> dict[str, int]:
        counts = {}
        for bound in self.buckets:
            counts[f"le_{bound}"] = sum(1 for v in self._observations if v <= bound)
        counts["le_inf"] = len(self._observations)
        return counts


class MetricsCollector:
    """Central metrics collector for TaskFlow.

    Tracks:
    - Task creation, completion, and failure counts
    - Task execution duration histograms
    - Active task gauge
    - API request counts and latencies
    - Queue depth

    Metrics are exposed in Prometheus text format via the /metrics endpoint.

    Example:
        collector = MetricsCollector()
        collector.task_created(executor="default", priority="normal")
        collector.task_completed(executor="default", duration=1.23)
        print(collector.export())
    """

    def __init__(self) -> None:
        self.tasks_created = Counter(
            "taskflow_tasks_created_total",
            "Total number of tasks created",
            labels=["executor", "priority"],
        )
        self.tasks_completed = Counter(
            "taskflow_tasks_completed_total",
            "Total number of tasks completed",
            labels=["executor", "status"],
        )
        self.task_duration = Histogram(
            "taskflow_task_duration_seconds",
            "Task execution duration in seconds",
        )
        self.api_requests = Counter(
            "taskflow_api_requests_total",
            "Total API requests",
            labels=["method", "endpoint", "status_code"],
        )
        self._start_time = time.monotonic()

    def task_created(self, executor: str = "default", priority: str = "normal") -> None:
        """Record a task creation."""
        self.tasks_created.inc(executor=executor, priority=priority)

    def task_completed(self, executor: str = "default", duration: float = 0.0,
                       status: str = "completed") -> None:
        """Record a task completion."""
        self.tasks_completed.inc(executor=executor, status=status)
        if duration > 0:
            self.task_duration.observe(duration)

    def api_request(self, method: str, endpoint: str, status_code: int) -> None:
        """Record an API request."""
        self.api_requests.inc(method=method, endpoint=endpoint, status_code=str(status_code))

    def get_uptime_seconds(self) -> float:
        """Get collector uptime in seconds."""
        return time.monotonic() - self._start_time

    def export(self) -> str:
        """Export metrics in Prometheus text format."""
        lines: list[str] = []

        # Tasks created
        lines.append(f"# HELP {self.tasks_created.name} {self.tasks_created.description}")
        lines.append(f"# TYPE {self.tasks_created.name} counter")
        for labels, value in self.tasks_created._values.items():
            label_str = ",".join(f'{k}="{v}"' for k, v in zip(self.tasks_created.labels, labels))
            lines.append(f"{self.tasks_created.name}{{{label_str}}} {value}")

        # Task duration histogram
        lines.append(f"# HELP {self.task_duration.name} {self.task_duration.description}")
        lines.append(f"# TYPE {self.task_duration.name} histogram")
        bucket_counts = self.task_duration.get_bucket_counts()
        for bucket, count in bucket_counts.items():
            bound = bucket.replace("le_", "")
            lines.append(f'{self.task_duration.name}_bucket{{le="{bound}"}} {count}')
        lines.append(f"{self.task_duration.name}_count {self.task_duration.count}")
        lines.append(f"{self.task_duration.name}_sum {self.task_duration.sum:.6f}")

        return "\n".join(lines) + "\n"

    def get_summary(self) -> dict[str, Any]:
        """Get a JSON-friendly summary of all metrics."""
        return {
            "uptime_seconds": round(self.get_uptime_seconds(), 2),
            "tasks_created": dict(self.tasks_created._values),
            "tasks_completed": dict(self.tasks_completed._values),
            "task_duration": {
                "count": self.task_duration.count,
                "sum": round(self.task_duration.sum, 4),
                "buckets": self.task_duration.get_bucket_counts(),
            },
        }
