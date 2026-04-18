# Blocker Report — agentkit-cli v0.97.2 optimize unblock and finalize

Date: 2026-04-18
Contract: all-day-build-contract-agentkit-cli-v0.97.2-optimize-unblock-and-finalize.md

## Status

Stopped after completing the scoped pages/docs diagnosis because the required full-suite gate exposed two additional failure classes outside the pages/docs unblock scope.

## What Passed

- Pages/docs diagnosis confirmed the stale-surface blocker is already repaired in this worktree.
- `uv run pytest -q tests/test_pages_refresh.py tests/test_pages_sync_d4.py` -> `60 passed in 0.96s`
- `uv run pytest -q tests/test_optimize_smoke.py tests/test_optimize_d2_hardening.py tests/test_optimize_realworld.py tests/test_optimize_d4.py` -> `24 passed in 0.45s`

## Blocking Failures

`uv run pytest -q` -> `2 failed, 4757 passed, 1 warning in 376.91s (0:06:16)`

### Failure class 1: optimize renderer expectation drift
- `tests/test_optimize_d3.py::test_text_renderer_is_reviewable`
- Expected: `Verdict: Changes available`
- Actual: `Verdict: Meaningful rewrite available`
- Current source: `agentkit_cli/renderers/optimize_renderer.py` prints `result.verdict` directly, and the optimize surface has already moved to the newer verdict wording used by the smoke/guardrail pass.

### Failure class 2: watch debounce timing flake
- `tests/test_watch.py::TestChangeHandler::test_last_file_recorded`
- Observed error: `IndexError: list index out of range`
- Current source: `agentkit_cli/commands/watch.py`
- The test assumes the debounced timer fires within `0.15s` after two immediate writes with a `0.05s` debounce, but this run produced no recorded callback before the assertion.

## Why Stopped

The contract says to stop if the full suite remains red for a second unrelated failure class after the pages repair. Both remaining failures are outside the intended pages/docs unblock plus held-back v0.97.2 handoff scope, so continuing would widen scope.

## Recommended Next Step

Run a separate narrow pass to resolve:
1. whether `tests/test_optimize_d3.py` should be updated to the current verdict language or the renderer should preserve the older label, and
2. whether the watch debounce test needs a less timing-sensitive assertion or the handler needs stronger timer synchronization.
