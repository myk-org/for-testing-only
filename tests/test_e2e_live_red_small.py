"""E2E live verification: red tox, output under GitHub's 65535-byte cap."""


def test_deliberate_failure_small_output() -> None:
    assert 1 + 1 == 3, "E2E-RED-SMALL-REASON: deliberate failure, small output"