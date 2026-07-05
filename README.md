# TaskFlow

A lightweight task orchestration framework with plugin support, scheduling, and real-time monitoring.

## Features

- **Task Pipelines** — Define multi-step workflows as DAGs with dependency resolution
- **Plugin System** — Extend with custom executors, notifiers, and storage backends
- **Scheduling** — Cron-based and interval scheduling with timezone support
- **Real-time Monitoring** — WebSocket-based dashboard with live task progress
- **Retry & Circuit Breaking** — Configurable retry policies with exponential backoff
- **Multi-tenant** — Isolated workspaces with RBAC and API key authentication
- **Metrics** — Prometheus-compatible metrics for task duration, throughput, and error rates

## Quick Start

```bash
# Install
pip install taskflow

# Start the server
taskflow server --port 8000

# Start a worker
taskflow-worker --concurrency 4

# Create a task via CLI
taskflow run my-pipeline --input data.json
```

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   REST API   │────▶│   Scheduler  │────▶│   Workers    │
│  (FastAPI)   │     │  (Celery)    │     │  (Executors) │
└──────┬───────┘     └──────────────┘     └──────┬───────┘
       │                                         │
       ▼                                         ▼
┌──────────────┐                          ┌──────────────┐
│   Storage    │                          │   Plugins    │
│  (SQL/Redis) │                          │  (Registry)  │
└──────────────┘                          └──────────────┘
```

## Configuration

TaskFlow is configured via `taskflow.toml` or environment variables:

```toml
[server]
host = "0.0.0.0"
port = 8000
workers = 4

[database]
url = "postgresql://localhost/taskflow"
pool_size = 10

[redis]
url = "redis://localhost:6379/0"

[scheduler]
timezone = "UTC"
max_concurrent_tasks = 50

[security]
secret_key = "${TASKFLOW_SECRET_KEY}"
api_key_header = "X-API-Key"
session_ttl = 3600
```

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tasks` | GET | List all tasks with filtering |
| `/api/tasks` | POST | Create a new task |
| `/api/tasks/{id}` | GET | Get task details and status |
| `/api/tasks/{id}/cancel` | POST | Cancel a running task |
| `/api/pipelines` | GET | List pipeline definitions |
| `/api/pipelines` | POST | Create a pipeline |
| `/api/pipelines/{id}/run` | POST | Trigger a pipeline run |
| `/api/metrics` | GET | Prometheus metrics endpoint |
| `/api/health` | GET | Health check |
| `/ws/tasks` | WS | Real-time task updates |

## Plugin Development

```python
from taskflow.plugins import ExecutorPlugin, hookimpl

class MyExecutor(ExecutorPlugin):
    name = "my-executor"

    @hookimpl
    def execute_task(self, task, context):
        # Your custom execution logic
        result = do_work(task.payload)
        return {"status": "completed", "output": result}

    @hookimpl
    def on_task_failure(self, task, error):
        notify_team(f"Task {task.id} failed: {error}")
```

## License

MIT
