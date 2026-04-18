# Progress Log, v0.98.0 Mainline Sync

## D1. Source-of-truth map and import plan
- Read the build contract and current README.
- Compared `origin/main...release/v0.98.0` and mapped the shipped surfaces that matter for this sync.
- Confirmed the recoverable product scope is concentrated in release-check hardening, optimize command/repo-sweep support, improve/run wiring, tests/fixtures, and a final site/docs reconciliation commit.
- Explicitly excluded unrelated release-branch noise: long generated site refresh chains, extra progress logs, and unrelated posting-script changes.
- Verification: inspected the release-only file list, release-only commit list, and the main diffs for optimize/release-check/test surfaces.
- Environment note: the contract asks for helper scripts (`scripts/pre-action-recall.sh`, `scripts/check-status-conflicts.sh`, `scripts/post-agent-hygiene-check.sh`) that do not exist in this worktree, so final validation will rely on the available test suite plus git hygiene checks.

## D2a. Release-check hardening sync
- Cherry-picked the shipped release-check hardening series from the release line onto this mainline sync branch.
- Recovered the rewritten release-check engine, richer markdown/export path, run-command integration, command wiring updates, and the release-check/run/main tests that shipped with v0.98.0.
- Verification: `uv run pytest -q --tb=no tests/test_release_check.py tests/test_run_command.py tests/test_main.py` passed with 34 tests green.
- Note: the first attempt used system `python3 -m pytest`, but this branch expects the repo-managed `uv run pytest` environment, so I switched to that and it passed.

## D2b. Optimize and improve/run integration sync
- Cherry-picked the shipped optimize series from the release line, including the engine, CLI wiring, review renderer, repo sweep support, protected-section hardening, improve integration, real-world fixture pack, smoke harness, and the validation fixes that shipped with the release branch.
- Kept the branch clean while resolving repeated conflicts only in the release branch `progress-log.md`, always preferring this branch's existing file so product code/tests stayed source-of-truth.
- Reverted generated noise after test runs (`__pycache__`, `uv.lock`) instead of carrying it forward.
- Verification: `uv run pytest -q --tb=no tests/test_optimize_d1.py tests/test_optimize_d2.py tests/test_optimize_d2_hardening.py tests/test_optimize_d3.py tests/test_optimize_d4.py tests/test_optimize_realworld.py tests/test_optimize_smoke.py tests/test_release_check.py tests/test_run_command.py tests/test_main.py` passed with 76 tests green.

## Next
- Reconcile the minimal docs/site surfaces and then run full validation.
