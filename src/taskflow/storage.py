"""Persistent storage layer for tasks and pipelines."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from taskflow.models import (
    Pipeline,
    PipelineRun,
    Task,
    TaskDefinition,
    TaskPriority,
    TaskStatus,
)

logger = logging.getLogger(__name__)

# Table names — single source of truth
TABLE_TASKS = "tasks"
TABLE_PIPELINES = "pipelines"
TABLE_PIPELINE_RUNS = "pipeline_runs"
TABLE_SCHEDULES = "schedules"

# Query limits
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


class TaskFilter:
    """Filtering options for task queries."""

    def __init__(
        self,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        executor: str | None = None,
        tags: list[str] | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> None:
        self.status = status
        self.priority = priority
        self.executor = executor
        self.tags = tags
        self.created_after = created_after
        self.created_before = created_before
        self.limit = min(limit, MAX_PAGE_SIZE)
        self.offset = max(offset, 0)


class TaskStore:
    """In-memory task store with query and lifecycle support.

    In production, this would be backed by PostgreSQL or another
    database. This implementation uses dictionaries for simplicity
    and is suitable for testing and development.

    Thread safety: This store is NOT thread-safe. Use a lock or
    an async-safe implementation for concurrent access.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._pipelines: dict[str, Pipeline] = {}
        self._runs: dict[str, PipelineRun] = {}

    def save_task(self, task: Task) -> Task:
        """Save or update a task."""
        self._tasks[task.id] = task
        logger.debug("Saved task %s (status=%s)", task.id, task.status)
        return task

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def delete_task(self, task_id: str) -> bool:
        """Delete a task. Returns True if found and deleted."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def list_tasks(self, filter: TaskFilter | None = None) -> list[Task]:
        """List tasks with optional filtering."""
        tasks = list(self._tasks.values())

        if filter:
            if filter.status:
                tasks = [t for t in tasks if t.status == filter.status]
            if filter.priority:
                tasks = [t for t in tasks if t.definition.priority == filter.priority]
            if filter.executor:
                tasks = [t for t in tasks if t.definition.executor == filter.executor]
            if filter.tags:
                tag_set = set(filter.tags)
                tasks = [t for t in tasks if tag_set.issubset(set(t.definition.tags))]
            if filter.created_after:
                tasks = [t for t in tasks if t.created_at >= filter.created_after]
            if filter.created_before:
                tasks = [t for t in tasks if t.created_at <= filter.created_before]

            # Sort by creation time descending
            tasks.sort(key=lambda t: t.created_at, reverse=True)

            # Apply pagination
            tasks = tasks[filter.offset : filter.offset + filter.limit]

        return tasks

    def count_tasks(self, status: TaskStatus | None = None) -> int:
        """Count tasks, optionally filtered by status."""
        if status is None:
            return len(self._tasks)
        return sum(1 for t in self._tasks.values() if t.status == status)

    def save_pipeline(self, pipeline: Pipeline) -> Pipeline:
        """Save or update a pipeline definition."""
        self._pipelines[pipeline.id] = pipeline
        return pipeline

    def get_pipeline(self, pipeline_id: str) -> Pipeline | None:
        """Get a pipeline by ID."""
        return self._pipelines.get(pipeline_id)

    def list_pipelines(self) -> list[Pipeline]:
        """List all pipeline definitions."""
        return list(self._pipelines.values())

    def save_run(self, run: PipelineRun) -> PipelineRun:
        """Save or update a pipeline run."""
        self._runs[run.id] = run
        return run

    def get_run(self, run_id: str) -> PipelineRun | None:
        """Get a pipeline run by ID."""
        return self._runs.get(run_id)

    def get_stats(self) -> dict[str, Any]:
        """Get storage statistics."""
        status_counts = {}
        for task in self._tasks.values():
            status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1

        return {
            "total_tasks": len(self._tasks),
            "tasks_by_status": status_counts,
            "total_pipelines": len(self._pipelines),
            "total_runs": len(self._runs),
        }
