"""Core data models for TaskFlow."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Possible states for a task in its lifecycle."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(str, Enum):
    """Task execution priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


PRIORITY_WEIGHTS: dict[TaskPriority, int] = {
    TaskPriority.LOW: 1,
    TaskPriority.NORMAL: 5,
    TaskPriority.HIGH: 10,
    TaskPriority.CRITICAL: 100,
}

MAX_RETRY_ATTEMPTS = 5
DEFAULT_TIMEOUT_SECONDS = 300
TASK_ID_PREFIX = "tf-"


class RetryPolicy(BaseModel):
    """Configuration for automatic task retry behavior."""

    max_attempts: int = Field(default=3, ge=1, le=MAX_RETRY_ATTEMPTS)
    delay_seconds: float = Field(default=1.0, ge=0.1)
    backoff_multiplier: float = Field(default=2.0, ge=1.0)
    max_delay_seconds: float = Field(default=60.0)
    retry_on: list[str] = Field(default_factory=lambda: ["TimeoutError", "ConnectionError"])

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number using exponential backoff."""
        delay = self.delay_seconds * (self.backoff_multiplier ** (attempt - 1))
        return min(delay, self.max_delay_seconds)


class TaskDefinition(BaseModel):
    """Schema for creating a new task."""

    name: str = Field(min_length=1, max_length=255)
    executor: str = Field(default="default")
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    timeout_seconds: int = Field(default=DEFAULT_TIMEOUT_SECONDS, ge=1)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    tags: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class Task(BaseModel):
    """A task instance with full lifecycle state."""

    id: str = Field(default_factory=lambda: f"{TASK_ID_PREFIX}{uuid4().hex[:12]}")
    definition: TaskDefinition
    status: TaskStatus = TaskStatus.PENDING
    attempt: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    worker_id: str | None = None
    duration_seconds: float | None = None

    @property
    def is_terminal(self) -> bool:
        """Check if the task is in a terminal state."""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)

    @property
    def is_retryable(self) -> bool:
        """Check if the task can be retried."""
        return (
            self.status == TaskStatus.FAILED
            and self.attempt < self.definition.retry_policy.max_attempts
        )


class PipelineStep(BaseModel):
    """A single step in a pipeline definition."""

    name: str
    task: TaskDefinition
    depends_on: list[str] = Field(default_factory=list)
    condition: str | None = None  # SpEL-like expression


class Pipeline(BaseModel):
    """A multi-step workflow definition executed as a DAG."""

    id: str = Field(default_factory=lambda: f"pipe-{uuid4().hex[:8]}")
    name: str
    description: str = ""
    steps: list[PipelineStep]
    max_parallel: int = Field(default=5, ge=1)
    timeout_seconds: int = Field(default=3600)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PipelineRun(BaseModel):
    """An execution instance of a pipeline."""

    id: str = Field(default_factory=lambda: f"run-{uuid4().hex[:8]}")
    pipeline_id: str
    status: TaskStatus = TaskStatus.PENDING
    step_results: dict[str, Task] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    triggered_by: str = "api"
