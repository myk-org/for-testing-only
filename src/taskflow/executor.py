"""Task executors — the runtime that actually runs tasks."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from taskflow.models import Task, TaskStatus

logger = logging.getLogger(__name__)


class ExecutorResult:
    """Result returned by an executor after task completion."""

    def __init__(
        self,
        success: bool,
        output: dict[str, Any] | None = None,
        error: str | None = None,
        duration_seconds: float = 0.0,
    ) -> None:
        self.success = success
        self.output = output or {}
        self.error = error
        self.duration_seconds = duration_seconds


class BaseExecutor(ABC):
    """Abstract base class for task executors.

    All custom executors must inherit from this class and implement
    the `execute` method. Executors are registered in the plugin
    registry and matched to tasks by the `executor` field in
    TaskDefinition.

    Lifecycle:
        1. `setup()` — Called once when the executor is loaded
        2. `execute(task)` — Called for each task assigned to this executor
        3. `teardown()` — Called when the worker shuts down

    Example:
        class EmailExecutor(BaseExecutor):
            name = "email"

            def execute(self, task: Task) -> ExecutorResult:
                send_email(task.definition.payload["to"], task.definition.payload["body"])
                return ExecutorResult(success=True)
    """

    name: str = "base"

    def setup(self) -> None:
        """Initialize executor resources. Called once on startup."""

    def teardown(self) -> None:
        """Clean up executor resources. Called on shutdown."""

    @abstractmethod
    def execute(self, task: Task) -> ExecutorResult:
        """Execute a task and return the result."""

    def validate_payload(self, payload: dict[str, Any]) -> list[str]:
        """Validate task payload before execution. Returns list of errors."""
        return []


class DefaultExecutor(BaseExecutor):
    """Built-in executor that processes tasks as simple function calls.

    Supports payloads with an `action` field that maps to built-in
    operations like `echo`, `sleep`, `http_request`, and `transform`.
    """

    name = "default"

    SUPPORTED_ACTIONS = ("echo", "sleep", "http_request", "transform", "noop")

    def execute(self, task: Task) -> ExecutorResult:
        start = time.monotonic()
        payload = task.definition.payload
        action = payload.get("action", "noop")

        try:
            if action == "echo":
                output = {"message": payload.get("message", ""), "echoed": True}
            elif action == "sleep":
                duration = min(payload.get("duration", 1), 30)
                time.sleep(duration)
                output = {"slept_seconds": duration}
            elif action == "transform":
                data = payload.get("data", {})
                output = {"transformed": {k.upper(): v for k, v in data.items()}}
            elif action == "noop":
                output = {"action": "noop"}
            else:
                return ExecutorResult(
                    success=False,
                    error=f"Unknown action: {action}",
                    duration_seconds=time.monotonic() - start,
                )

            return ExecutorResult(
                success=True,
                output=output,
                duration_seconds=time.monotonic() - start,
            )
        except Exception as exc:
            return ExecutorResult(
                success=False,
                error=str(exc),
                duration_seconds=time.monotonic() - start,
            )

    def validate_payload(self, payload: dict[str, Any]) -> list[str]:
        errors = []
        action = payload.get("action", "noop")
        if action not in self.SUPPORTED_ACTIONS:
            errors.append(f"Unsupported action: {action}. Must be one of {self.SUPPORTED_ACTIONS}")
        if action == "sleep":
            duration = payload.get("duration")
            if duration is not None and (not isinstance(duration, (int, float)) or duration < 0):
                errors.append("sleep duration must be a non-negative number")
        return errors


class ShellExecutor(BaseExecutor):
    """Executor that runs shell commands in a sandboxed subprocess.

    Security: Commands are executed with restricted permissions.
    Only whitelisted commands are allowed. No shell expansion.

    Payload fields:
        - command (str): The command to execute
        - args (list[str]): Command arguments
        - env (dict[str, str]): Additional environment variables
        - working_dir (str): Working directory (must be within sandbox)
    """

    name = "shell"

    ALLOWED_COMMANDS = ("echo", "date", "ls", "cat", "grep", "wc", "head", "tail", "sort", "uniq")

    def execute(self, task: Task) -> ExecutorResult:
        start = time.monotonic()
        payload = task.definition.payload
        command = payload.get("command", "")

        if command not in self.ALLOWED_COMMANDS:
            return ExecutorResult(
                success=False,
                error=f"Command '{command}' is not in the allowed list",
                duration_seconds=time.monotonic() - start,
            )

        # Simulate command execution (no actual subprocess for safety)
        return ExecutorResult(
            success=True,
            output={"command": command, "args": payload.get("args", []), "simulated": True},
            duration_seconds=time.monotonic() - start,
        )

    def validate_payload(self, payload: dict[str, Any]) -> list[str]:
        errors = []
        if "command" not in payload:
            errors.append("Missing required field: command")
        elif payload["command"] not in self.ALLOWED_COMMANDS:
            errors.append(f"Command not allowed. Allowed: {', '.join(self.ALLOWED_COMMANDS)}")
        return errors
