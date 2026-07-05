"""Command-line interface for TaskFlow."""

from __future__ import annotations

import json
import sys
from typing import Any


# CLI exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_USAGE = 2


def main(args: list[str] | None = None) -> int:
    """Main entry point for the taskflow CLI.

    Usage:
        taskflow server [--port PORT] [--host HOST]
        taskflow run PIPELINE [--input FILE] [--wait]
        taskflow status TASK_ID
        taskflow cancel TASK_ID
        taskflow list [--status STATUS] [--limit N]
        taskflow config [--show | --set KEY=VALUE]
        taskflow version
    """
    if args is None:
        args = sys.argv[1:]

    if not args:
        print_help()
        return EXIT_USAGE

    command = args[0]
    rest = args[1:]

    commands: dict[str, Any] = {
        "server": cmd_server,
        "run": cmd_run,
        "status": cmd_status,
        "cancel": cmd_cancel,
        "list": cmd_list,
        "config": cmd_config,
        "version": cmd_version,
        "help": lambda _: print_help() or EXIT_SUCCESS,
    }

    handler = commands.get(command)
    if handler is None:
        print(f"Unknown command: {command}", file=sys.stderr)
        print_help()
        return EXIT_USAGE

    return handler(rest)


def print_help() -> None:
    """Print CLI help text."""
    print("""TaskFlow — Task Orchestration Framework

Usage:
    taskflow <command> [options]

Commands:
    server      Start the TaskFlow API server
    run         Trigger a pipeline run
    status      Check task or pipeline status
    cancel      Cancel a running task
    list        List tasks with optional filters
    config      View or update configuration
    version     Show version information
    help        Show this help message

Run 'taskflow <command> --help' for command-specific help.
""")


def cmd_server(args: list[str]) -> int:
    """Start the API server."""
    port = 8000
    host = "0.0.0.0"

    i = 0
    while i < len(args):
        if args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        elif args[i] == "--host" and i + 1 < len(args):
            host = args[i + 1]
            i += 2
        else:
            i += 1

    print(f"Starting TaskFlow server on {host}:{port}")
    return EXIT_SUCCESS


def cmd_run(args: list[str]) -> int:
    """Trigger a pipeline run."""
    if not args:
        print("Error: pipeline name required", file=sys.stderr)
        return EXIT_USAGE

    pipeline_name = args[0]
    input_file = None
    wait = False

    i = 1
    while i < len(args):
        if args[i] == "--input" and i + 1 < len(args):
            input_file = args[i + 1]
            i += 2
        elif args[i] == "--wait":
            wait = True
            i += 1
        else:
            i += 1

    print(f"Running pipeline: {pipeline_name}")
    if input_file:
        print(f"Input file: {input_file}")
    if wait:
        print("Waiting for completion...")

    return EXIT_SUCCESS


def cmd_status(args: list[str]) -> int:
    """Check task status."""
    if not args:
        print("Error: task ID required", file=sys.stderr)
        return EXIT_USAGE

    task_id = args[0]
    print(json.dumps({"task_id": task_id, "status": "pending"}, indent=2))
    return EXIT_SUCCESS


def cmd_cancel(args: list[str]) -> int:
    """Cancel a running task."""
    if not args:
        print("Error: task ID required", file=sys.stderr)
        return EXIT_USAGE

    task_id = args[0]
    print(f"Cancelled task: {task_id}")
    return EXIT_SUCCESS


def cmd_list(args: list[str]) -> int:
    """List tasks."""
    status_filter = None
    limit = 50

    i = 0
    while i < len(args):
        if args[i] == "--status" and i + 1 < len(args):
            status_filter = args[i + 1]
            i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        else:
            i += 1

    print(json.dumps({"tasks": [], "total": 0, "filter": status_filter, "limit": limit}, indent=2))
    return EXIT_SUCCESS


def cmd_config(args: list[str]) -> int:
    """View or update configuration."""
    print(json.dumps({
        "server": {"host": "0.0.0.0", "port": 8000},
        "database": {"url": "sqlite:///taskflow.db"},
        "scheduler": {"timezone": "UTC", "max_concurrent": 50},
    }, indent=2))
    return EXIT_SUCCESS


def cmd_version(_args: list[str]) -> int:
    """Show version."""
    print("TaskFlow v2.4.1")
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
