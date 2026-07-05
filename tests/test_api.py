"""Tests for TaskFlow REST API."""

from taskflow.api import TaskAPI, HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from taskflow.storage import TaskStore


class TestTaskAPI:
    def setup_method(self):
        self.store = TaskStore()
        self.api = TaskAPI(self.store)

    def test_create_task(self):
        status, body = self.api.create_task({"name": "test-task"})
        assert status == HTTP_201_CREATED
        assert body["definition"]["name"] == "test-task"
        assert body["status"] == "pending"

    def test_get_task(self):
        _, created = self.api.create_task({"name": "find-me"})
        task_id = created["id"]

        status, body = self.api.get_task(task_id)
        assert status == HTTP_200_OK
        assert body["id"] == task_id

    def test_get_missing_task(self):
        status, body = self.api.get_task("nonexistent")
        assert status == HTTP_404_NOT_FOUND

    def test_list_tasks(self):
        self.api.create_task({"name": "task-1"})
        self.api.create_task({"name": "task-2"})

        status, body = self.api.list_tasks()
        assert status == HTTP_200_OK
        assert body["total"] == 2

    def test_cancel_task(self):
        _, created = self.api.create_task({"name": "cancel-me"})
        status, body = self.api.cancel_task(created["id"])
        assert status == HTTP_200_OK
        assert body["status"] == "cancelled"

    def test_cancel_completed_task_conflicts(self):
        _, created = self.api.create_task({"name": "done-task"})
        task = self.store.get_task(created["id"])
        from taskflow.models import TaskStatus
        task.status = TaskStatus.COMPLETED
        self.store.save_task(task)

        status, _ = self.api.cancel_task(created["id"])
        assert status == HTTP_409_CONFLICT

    def test_health_check(self):
        status, body = self.api.health_check()
        assert status == HTTP_200_OK
        assert body["status"] == "healthy"
        assert "version" in body
