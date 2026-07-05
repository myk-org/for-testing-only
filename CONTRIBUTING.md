# Contributing to TaskFlow

## Development Setup

```bash
git clone https://github.com/myk-org/for-testing-only.git
cd for-testing-only
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

## Code Style

- We use `ruff` for linting and formatting
- Type hints are required for all public functions
- All public classes need docstrings

## Adding a New Executor

1. Create a class inheriting from `BaseExecutor` in `src/taskflow/executor.py`
2. Implement the `execute(task)` method
3. Optionally override `validate_payload()` for input validation
4. Register in the plugin registry or via `worker.register_executor()`
5. Add tests in `tests/`

## Adding a Notifier Plugin

1. Create a class inheriting from `NotifierPlugin` in `src/taskflow/plugins.py`
2. Implement `notify(event, task, details)`
3. Optionally override `supports_event()` to filter events
4. Register via `PluginRegistry.register_notifier()`

## Pull Request Guidelines

- One feature per PR
- Include tests for new functionality
- Update README if adding user-facing features
- Squash commits before merge
