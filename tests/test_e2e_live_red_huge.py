"""E2E live verification: red tox, output over GitHub's 65535-byte cap."""


def test_deliberate_failure_huge_output() -> None:
    raise AssertionError("E2E-RED-HUGE-REASON\n" + ("\u2714" * 40000) + "\nE2E-TAIL-MARKER-END")