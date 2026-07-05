"""Task worker that pulls and executes tasks from the queue."""

from __future__ import annotations

import logging
import time
from typing import Any

from taskflow.executor import BaseExecutor, DefaultExecutor, ExecutorResult
from taskflow.models import Task, TaskStatus
from taskflow.plugins import PluginRegistry

logger = logging.getLogger(__name__)

# Worker defaults
DEFAULT_CONCURRENCY = 4
MAX_CONCURRENCY = 32
POLL_INTERVAL_SECONDS = 1.0
HEARTBEAT_INTERVAL_SECONDS = 30.0


class WorkerConfig:
    """Configuration for a TaskFlow worker process."""

    def __init__(
        self,
        concurrency: int = DEFAULT_CONCURRENCY,
        poll_interval: float = POLL_INTERVAL_SECONDS,
        executors: list[str] | None = None,
        worker_id: str | None = None,
    ) -> None:
        self.concurrency = min(max(concurrency, 1), MAX_CONCURRENCY)
        self.poll_interval = poll_interval
        self.executors = executors or ["default"]
        self.worker_id = worker_id or f"worker-{id(self):x}"


class Worker:
    """Executes tasks by polling a queue and dispatching to executors.

    The worker maintains a pool of executor instances and matches
    incoming tasks to the appropriate executor based on the task's
    `executor` field.

    Lifecycle:
        1. start() — Begin polling for tasks
        2. process_task(task) — Execute a single task
        3. stop() — Graceful shutdown

    Circuit Breaking:
        The worker tracks consecutive failures per executor. After
        5 consecutive failures, the executor is temporarily disabled
        for 60 seconds to prevent cascading failures.

    Example:
        worker = Worker(config=WorkerConfig(concurrency=4))
        worker.register_executor(DefaultExecutor())
        await worker.start()
    """

    CIRCUIT_BREAKER_THRESHOLD = 5
    CIRCUIT_BREAKER_TIMEOUT = 60.0  # seconds

    def __init__(self, config: WorkerConfig | None = None) -> None:
        self.config = config or WorkerConfig()
        self._executors: dict[str, BaseExecutor] = {}
        self._running_tasks: dict[str, Task] = {}
        self._is_running = False
        self._tasks_processed = 0
        self._tasks_failed = 0
        self._consecutive_failures: dict[str, int] = {}
        self._circuit_open_until: dict[str, float] = {}

    def register_executor(self, executor: BaseExecutor) -> None:
        """Register an executor instance."""
        executor.setup()
        self._executors[executor.name] = executor
        self._consecutive_failures[executor.name] = 0
        logger.info("Registered executor: %s", executor.name)

    def process_task(self, task: Task) -> ExecutorResult:
        """Process a single task through its assigned executor.

        Steps:
            1. Validate executor exists and circuit is closed
            2. Validate task payload
            3. Update task status to RUNNING
            4. Execute with timeout tracking
            5. Update task status based on result
            6. Handle retry if applicable

        Returns:
            ExecutorResult with success/failure details
        """
        executor_name = task.definition.executor
        executor = self._executors.get(executor_name)

        if executor is None:
            task.status = TaskStatus.FAILED
            task.error = f"No executor registered for '{executor_name}'"
            return ExecutorResult(success=False, error=task.error)

        # Check circuit breaker
        if self._is_circuit_open(executor_name):
            task.status = TaskStatus.FAILED
            task.error = f"Circuit breaker open for executor '{executor_name}'"
            return ExecutorResult(success=False, error=task.error)

        # Validate payload
        errors = executor.validate_payload(task.definition.payload)
        if errors:
            task.status = TaskStatus.FAILED
            task.error = f"Payload validation failed: {'; '.join(errors)}"
            return ExecutorResult(success=False, error=task.error)

        # Execute
        task.status = TaskStatus.RUNNING
        task.attempt += 1
        task.worker_id = self.config.worker_id

        start_time = time.monotonic()
        result = executor.execute(task)
        task.duration_seconds = time.monotonic() - start_time

        if result.success:
            task.status = TaskStatus.COMPLETED
            task.result = result.output
            self._tasks_processed += 1
            self._consecutive_failures[executor_name] = 0
        else:
            self._tasks_failed += 1
            self._consecutive_failures[executor_name] = (
                self._consecutive_failures.get(executor_name, 0) + 1
            )

            # Check if circuit breaker should open
            if self._consecutive_failures[executor_name] >= self.CIRCUIT_BREAKER_THRESHOLD:
                self._circuit_open_until[executor_name] = (
                    time.monotonic() + self.CIRCUIT_BREAKER_TIMEOUT
                )
                logger.warning("Circuit breaker opened for executor '%s'", executor_name)

            if task.is_retryable:
                task.status = TaskStatus.RETRYING
                task.error = result.error
            else:
                task.status = TaskStatus.FAILED
                task.error = result.error

        return result

    def _is_circuit_open(self, executor_name: str) -> bool:
        """Check if the circuit breaker is open for an executor."""
        deadline = self._circuit_open_until.get(executor_name, 0.0)
        if time.monotonic() < deadline:
            return True
        # Circuit is closed or has reset
        if executor_name in self._circuit_open_until:
            del self._circuit_open_until[executor_name]
            self._consecutive_failures[executor_name] = 0
        return False

    def get_stats(self) -> dict[str, Any]:
        """Get worker statistics."""
        return {
            "worker_id": self.config.worker_id,
            "concurrency": self.config.concurrency,
            "is_running": self._is_running,
            "tasks_processed": self._tasks_processed,
            "tasks_failed": self._tasks_failed,
            "active_tasks": len(self._running_tasks),
            "registered_executors": list(self._executors.keys()),
            "circuit_breakers": {
                name: "open" if self._is_circuit_open(name) else "closed"
                for name in self._executors
            },
        }


def start_worker(concurrency: int = DEFAULT_CONCURRENCY) -> None:
    """Entry point for the taskflow-worker command."""
    config = WorkerConfig(concurrency=concurrency)
    worker = Worker(config=config)
    worker.register_executor(DefaultExecutor())
    logger.info("Worker started: %s (concurrency=%d)", config.worker_id, config.concurrency)
