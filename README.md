# TEST REPOSITORY

This repository is used for integration testing of the GitHub Webhook Server.

## Structure

```
├── OWNERS              # Root level approvers/reviewers
├── src/
│   ├── OWNERS          # Source approvers/reviewers
│   └── backend/
│       ├── OWNERS      # Backend approvers/reviewers
│       └── api/
│           ├── OWNERS  # API approvers/reviewers
│           └── handler.py
├── tests/
│   ├── OWNERS          # Test approvers/reviewers
│   └── test_handler.py
├── tox.ini             # Tox configuration
└── Dockerfile          # Container build configuration
```

## Purpose

This repo validates:

- Nested OWNERS file discovery
- Pre-commit hook execution
- Tox test execution (pytest)
- Container build and push
- Python module installation (uv sync)
- Webhook processing flows

## How to Toggle Tests (Pass/Fail)

All tests check `VALIDATION_ENABLED` in `tests/config.py`:

```python
# tests/config.py
VALIDATION_ENABLED = True   # ← Change this to True/False
```

**To make tests PASS:**

```bash
# Set VALIDATION_ENABLED = True in tests/config.py
```

**To make tests FAIL:**

```bash
# Set VALIDATION_ENABLED = False in tests/config.py
```

This affects:

- ✅ **Pre-commit**: `.pre-commit-scripts/check_validation.py` checks this value
- ✅ **Tox/Pytest**: `tests/test_handler.py::test_validation_enabled` checks this value

## Testing Locally

```bash
# Install dependencies
uv sync

# Run pre-commit
prek run --all-files

# Run tox
uvx tox

# Run pytest
uv run pytest tests/ -v
```
