"""Plugin system for extending TaskFlow with custom executors and hooks."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from taskflow.models import Task

logger = logging.getLogger(__name__)


class PluginError(Exception):
    """Raised when a plugin fails to load or execute."""


class ExecutorPlugin(ABC):
    """Base class for executor plugins.

    Implement this to create custom task executors that can be
    registered and discovered by TaskFlow.

    Attributes:
        name: Unique plugin identifier used in task definitions.
        version: Semantic version string for the plugin.
    """

    name: str = "unnamed"
    version: str = "0.0.0"

    @abstractmethod
    def execute_task(self, task: Task, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a task with the given context."""

    def on_task_failure(self, task: Task, error: Exception) -> None:
        """Called when a task fails. Override for custom error handling."""

    def on_task_success(self, task: Task, result: dict[str, Any]) -> None:
        """Called when a task completes successfully."""

    def validate(self) -> list[str]:
        """Validate plugin configuration. Returns list of errors."""
        return []


class NotifierPlugin(ABC):
    """Base class for notification plugins.

    Implement this to send notifications on task lifecycle events
    (start, complete, fail, cancel).
    """

    name: str = "unnamed-notifier"

    @abstractmethod
    def notify(self, event: str, task: Task, details: dict[str, Any] | None = None) -> None:
        """Send a notification for a task event."""

    def supports_event(self, event: str) -> bool:
        """Check if this notifier handles a specific event type."""
        return True


class WebhookNotifier(NotifierPlugin):
    """Sends HTTP POST notifications to a configured webhook URL.

    Configuration:
        url: The webhook endpoint URL
        headers: Optional additional HTTP headers
        events: List of events to notify on (default: all)
        timeout: Request timeout in seconds
    """

    name = "webhook"

    def __init__(self, url: str, headers: dict[str, str] | None = None,
                 events: list[str] | None = None, timeout: int = 10) -> None:
        self.url = url
        self.headers = headers or {}
        self.events = events
        self.timeout = timeout

    def notify(self, event: str, task: Task, details: dict[str, Any] | None = None) -> None:
        """Send webhook notification (simulated)."""
        if self.events and event not in self.events:
            return
        logger.info("Webhook notification: event=%s task=%s url=%s", event, task.id, self.url)

    def supports_event(self, event: str) -> bool:
        if self.events is None:
            return True
        return event in self.events


class PluginRegistry:
    """Central registry for discovering and managing plugins.

    The registry handles plugin lifecycle:
    1. Registration — plugins are added by name
    2. Discovery — plugins are looked up by type and name
    3. Validation — all plugins are validated before use

    Example:
        registry = PluginRegistry()
        registry.register_executor(MyExecutor())
        registry.register_notifier(WebhookNotifier(url="https://example.com/hook"))

        executor = registry.get_executor("my-executor")
        notifiers = registry.get_notifiers_for_event("task.completed")
    """

    def __init__(self) -> None:
        self._executors: dict[str, ExecutorPlugin] = {}
        self._notifiers: dict[str, NotifierPlugin] = {}

    def register_executor(self, plugin: ExecutorPlugin) -> None:
        """Register an executor plugin."""
        if plugin.name in self._executors:
            raise PluginError(f"Executor '{plugin.name}' is already registered")
        errors = plugin.validate()
        if errors:
            raise PluginError(f"Plugin '{plugin.name}' validation failed: {'; '.join(errors)}")
        self._executors[plugin.name] = plugin
        logger.info("Registered executor plugin: %s v%s", plugin.name, plugin.version)

    def register_notifier(self, plugin: NotifierPlugin) -> None:
        """Register a notifier plugin."""
        if plugin.name in self._notifiers:
            raise PluginError(f"Notifier '{plugin.name}' is already registered")
        self._notifiers[plugin.name] = plugin
        logger.info("Registered notifier plugin: %s", plugin.name)

    def get_executor(self, name: str) -> ExecutorPlugin | None:
        """Look up an executor by name."""
        return self._executors.get(name)

    def get_notifiers_for_event(self, event: str) -> list[NotifierPlugin]:
        """Get all notifiers that handle a specific event."""
        return [n for n in self._notifiers.values() if n.supports_event(event)]

    def list_executors(self) -> list[dict[str, str]]:
        """List all registered executors."""
        return [{"name": p.name, "version": p.version} for p in self._executors.values()]

    def list_notifiers(self) -> list[dict[str, str]]:
        """List all registered notifiers."""
        return [{"name": p.name} for p in self._notifiers.values()]
