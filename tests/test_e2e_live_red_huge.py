"""E2E live verification: red tox, output genuinely over GitHub's 65535-byte cap.

Short lines on purpose: the per-line cap cannot save this, the log itself is ~300 KB,
so the failure section alone is over budget and the overflow policy has to kick in.
"""


def test_deliberate_failure_huge_multiline_output() -> None:
    detail = "\n".join(f"detail line {i} " + "x" * 80 for i in range(3000))
    raise AssertionError("E2E-RED-HUGE-REASON\n" + detail + "\nE2E-TAIL-MARKER-END")