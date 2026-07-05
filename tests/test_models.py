"""Tests for TaskFlow core models."""

from taskflow.models import (
    RetryPolicy,
    Task,
    TaskDefinition,
    TaskPriority,
    TaskStatus,
    PRIORITY_WEIGHTS,
    MAX_RETRY_ATTEMPTS,
)


class TestTaskStatus:
    def test_terminal_states(self):
        definition = TaskDefinition(name="test-task")
        for status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            task = Task(definition=definition, status=status)
            assert task.is_terminal

    def test_non_terminal_states(self):
        definition = TaskDefinition(name="test-task")
        for status in (TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RUNNING):
            task = Task(definition=definition, status=status)
            assert not task.is_terminal


class TestRetryPolicy:
    def test_exponential_backoff(self):
        policy = RetryPolicy(delay_seconds=1.0, backoff_multiplier=2.0)
        assert policy.get_delay(1) == 1.0
        assert policy.get_delay(2) == 2.0
        assert policy.get_delay(3) == 4.0

    def test_max_delay_cap(self):
        policy = RetryPolicy(delay_seconds=10.0, backoff_multiplier=3.0, max_delay_seconds=30.0)
        assert policy.get_delay(5) == 30.0  # Would be 810 without cap

    def test_retryable_task(self):
        policy = RetryPolicy(max_attempts=3)
        definition = TaskDefinition(name="retry-me", retry_policy=policy)
        task = Task(definition=definition, status=TaskStatus.FAILED, attempt=1)
        assert task.is_retryable

    def test_not_retryable_when_max_attempts(self):
        policy = RetryPolicy(max_attempts=3)
        definition = TaskDefinition(name="retry-me", retry_policy=policy)
        task = Task(definition=definition, status=TaskStatus.FAILED, attempt=3)
        assert not task.is_retryable


class TestTaskDefinition:
    def test_default_values(self):
        definition = TaskDefinition(name="simple")
        assert definition.executor == "default"
        assert definition.priority == TaskPriority.NORMAL
        assert definition.tags == []

    def test_priority_weights(self):
        assert PRIORITY_WEIGHTS[TaskPriority.CRITICAL] > PRIORITY_WEIGHTS[TaskPriority.HIGH]
        assert PRIORITY_WEIGHTS[TaskPriority.HIGH] > PRIORITY_WEIGHTS[TaskPriority.NORMAL]

    def test_task_id_prefix(self):
        definition = TaskDefinition(name="test")
        task = Task(definition=definition)
        assert task.id.startswith("tf-")
