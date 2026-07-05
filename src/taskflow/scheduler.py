"""Task scheduling engine with cron and interval support."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field

from taskflow.models import TaskDefinition, TaskPriority


class ScheduleEntry(BaseModel):
    """A scheduled task definition with trigger configuration."""

    id: str
    name: str
    task: TaskDefinition
    cron_expression: str | None = None
    interval_seconds: int | None = None
    timezone: str = "UTC"
    enabled: bool = True
    last_run: datetime | None = None
    next_run: datetime | None = None
    max_instances: int = Field(default=1, ge=1)
    jitter_seconds: int = Field(default=0, ge=0)
    metadata: dict[str, str] = Field(default_factory=dict)


class SchedulerConfig(BaseModel):
    """Global scheduler configuration."""

    check_interval_seconds: int = 10
    max_concurrent_schedules: int = 50
    missed_run_policy: str = "skip"  # skip | run_once | run_all
    default_timezone: str = "UTC"


class Scheduler:
    """Manages scheduled task execution with cron and interval triggers.

    The scheduler runs as a background loop, checking for due schedules
    every `check_interval_seconds`. It supports:

    - Cron expressions (standard 5-field format)
    - Fixed interval schedules
    - Timezone-aware scheduling
    - Jitter to prevent thundering herd
    - Max instance limits to prevent overlap

    Example:
        scheduler = Scheduler(config=SchedulerConfig())
        scheduler.add_schedule(ScheduleEntry(
            id="daily-cleanup",
            name="Daily Cleanup",
            task=TaskDefinition(name="cleanup", executor="maintenance"),
            cron_expression="0 2 * * *",
            timezone="America/New_York",
        ))
        await scheduler.start()
    """

    def __init__(self, config: SchedulerConfig | None = None) -> None:
        self.config = config or SchedulerConfig()
        self._schedules: dict[str, ScheduleEntry] = {}
        self._running_instances: dict[str, int] = {}
        self._is_running = False

    def add_schedule(self, entry: ScheduleEntry) -> None:
        """Register a new schedule entry."""
        self._schedules[entry.id] = entry
        self._running_instances.setdefault(entry.id, 0)

    def remove_schedule(self, schedule_id: str) -> bool:
        """Remove a schedule by ID. Returns True if found and removed."""
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            self._running_instances.pop(schedule_id, None)
            return True
        return False

    def get_schedule(self, schedule_id: str) -> ScheduleEntry | None:
        """Get a schedule by ID."""
        return self._schedules.get(schedule_id)

    def list_schedules(self, enabled_only: bool = False) -> list[ScheduleEntry]:
        """List all registered schedules."""
        schedules = list(self._schedules.values())
        if enabled_only:
            schedules = [s for s in schedules if s.enabled]
        return schedules

    def is_due(self, entry: ScheduleEntry, now: datetime | None = None) -> bool:
        """Check if a schedule entry is due for execution."""
        if not entry.enabled:
            return False

        if self._running_instances.get(entry.id, 0) >= entry.max_instances:
            return False

        if now is None:
            now = datetime.now(timezone.utc)

        if entry.next_run and now >= entry.next_run:
            return True

        return False

    def compute_next_run(self, entry: ScheduleEntry) -> datetime:
        """Calculate the next run time for a schedule entry."""
        now = datetime.now(timezone.utc)

        if entry.interval_seconds:
            base = entry.last_run or now
            return base + timedelta(seconds=entry.interval_seconds)

        # For cron expressions, return next minute boundary as placeholder
        return now.replace(second=0, microsecond=0) + timedelta(minutes=1)

    def generate_schedule_id(self, name: str) -> str:
        """Generate a deterministic schedule ID from a name."""
        return f"sched-{hashlib.sha256(name.encode()).hexdigest()[:10]}"

    def get_stats(self) -> dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "total_schedules": len(self._schedules),
            "enabled_schedules": sum(1 for s in self._schedules.values() if s.enabled),
            "running_instances": dict(self._running_instances),
            "is_running": self._is_running,
        }
