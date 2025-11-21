#!/usr/bin/env python3
"""Pre-commit hook to check validation is enabled.

This script checks that VALIDATION_ENABLED = True in tests/config.py
- VALIDATION_ENABLED = True  -> pre-commit passes
- VALIDATION_ENABLED = False -> pre-commit fails
"""
import sys
from pathlib import Path


def main():
    """Check validation is enabled."""
    config_file = Path("tests/config.py")

    if not config_file.exists():
        print("ERROR: tests/config.py not found")
        return 1

    content = config_file.read_text()

    if "VALIDATION_ENABLED = True" in content:
        print("✓ Validation is enabled")
        return 0
    elif "VALIDATION_ENABLED = False" in content:
        print("✗ Validation is disabled - set VALIDATION_ENABLED = True in tests/config.py")
        return 1
    else:
        print("✗ VALIDATION_ENABLED not found in tests/config.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
