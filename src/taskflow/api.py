"""REST API endpoints for TaskFlow."""

from __future__ import annotations

from typing import Any

from taskflow.models import (
    Pipeline,
    PipelineRun,
    PipelineStep,
    Task,
    TaskDefinition,
    TaskStatus,
)
from taskflow.storage import TaskFilter, TaskStore

# API version prefix
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Response status codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409
HTTP_429_TOO_MANY = 429


class TaskAPI:
    """HTTP API handler for task operations.

    All methods return (status_code, body) tuples that can be
    mapped to HTTP responses by the web framework layer.

    Endpoints:
        POST   /tasks          — Create a new task
        GET    /tasks          — List tasks with filtering
        GET    /tasks/{id}     — Get task by ID
        POST   /tasks/{id}/cancel — Cancel a running task
        DELETE /tasks/{id}     — Delete a task

        POST   /pipelines      — Create a pipeline
        GET    /pipelines      — List pipelines
        POST   /pipelines/{id}/run — Start a pipeline run
        GET    /runs/{id}      — Get pipeline run status

        GET    /health         — Health check
        GET    /metrics        — Basic metrics
    """

    def __init__(self, store: TaskStore) -> None:
        self.store = store

    def create_task(self, data: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        """Create a new task from a request body."""
        try:
            definition = TaskDefinition(**data)
        except Exception as exc:
            return HTTP_400_BAD_REQUEST, {"error": f"Invalid task definition: {exc}"}

        task = Task(definition=definition)
        self.store.save_task(task)
        return HTTP_201_CREATED, task.model_dump(mode="json")

    def get_task(self, task_id: str) -> tuple[int, dict[str, Any]]:
        """Get a task by ID."""
        task = self.store.get_task(task_id)
        if task is None:
            return HTTP_404_NOT_FOUND, {"error": f"Task '{task_id}' not found"}
        return HTTP_200_OK, task.model_dump(mode="json")

    def list_tasks(
        self,
        status: str | None = None,
        priority: str | None = None,
        executor: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, dict[str, Any]]:
        """List tasks with optional filtering."""
        task_filter = TaskFilter(
            status=TaskStatus(status) if status else None,
            priority=None,
            executor=executor,
            limit=limit,
            offset=offset,
        )
        tasks = self.store.list_tasks(task_filter)
        total = self.store.count_tasks(task_filter.status)
        return HTTP_200_OK, {
            "tasks": [t.model_dump(mode="json") for t in tasks],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def cancel_task(self, task_id: str) -> tuple[int, dict[str, Any]]:
        """Cancel a running or pending task."""
        task = self.store.get_task(task_id)
        if task is None:
            return HTTP_404_NOT_FOUND, {"error": f"Task '{task_id}' not found"}

        if task.is_terminal:
            return HTTP_409_CONFLICT, {
                "error": f"Task is already in terminal state: {task.status.value}"
            }

        task.status = TaskStatus.CANCELLED
        self.store.save_task(task)
        return HTTP_200_OK, task.model_dump(mode="json")

    def delete_task(self, task_id: str) -> tuple[int, dict[str, Any]]:
        """Delete a task by ID."""
        if not self.store.delete_task(task_id):
            return HTTP_404_NOT_FOUND, {"error": f"Task '{task_id}' not found"}
        return HTTP_204_NO_CONTENT, {}

    def create_pipeline(self, data: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        """Create a new pipeline definition."""
        try:
            steps = [PipelineStep(**s) for s in data.get("steps", [])]
            pipeline = Pipeline(
                name=data["name"],
                description=data.get("description", ""),
                steps=steps,
                max_parallel=data.get("max_parallel", 5),
            )
        except Exception as exc:
            return HTTP_400_BAD_REQUEST, {"error": f"Invalid pipeline: {exc}"}

        self.store.save_pipeline(pipeline)
        return HTTP_201_CREATED, pipeline.model_dump(mode="json")

    def list_pipelines(self) -> tuple[int, dict[str, Any]]:
        """List all pipeline definitions."""
        pipelines = self.store.list_pipelines()
        return HTTP_200_OK, {
            "pipelines": [p.model_dump(mode="json") for p in pipelines],
            "total": len(pipelines),
        }

    def start_pipeline_run(self, pipeline_id: str) -> tuple[int, dict[str, Any]]:
        """Start a new pipeline run."""
        pipeline = self.store.get_pipeline(pipeline_id)
        if pipeline is None:
            return HTTP_404_NOT_FOUND, {"error": f"Pipeline '{pipeline_id}' not found"}

        run = PipelineRun(pipeline_id=pipeline_id, status=TaskStatus.QUEUED)
        self.store.save_run(run)
        return HTTP_201_CREATED, run.model_dump(mode="json")

    def get_run(self, run_id: str) -> tuple[int, dict[str, Any]]:
        """Get a pipeline run by ID."""
        run = self.store.get_run(run_id)
        if run is None:
            return HTTP_404_NOT_FOUND, {"error": f"Run '{run_id}' not found"}
        return HTTP_200_OK, run.model_dump(mode="json")

    def health_check(self) -> tuple[int, dict[str, Any]]:
        """Health check endpoint."""
        stats = self.store.get_stats()
        return HTTP_200_OK, {
            "status": "healthy",
            "version": "2.4.1",
            "storage": stats,
        }
