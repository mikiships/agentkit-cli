# Progress Log — agentkit-cli v1.18.0 relaunch lanes

## D4 complete: four-surface release checklist finished, v1.18.0 shipped

**What changed:**
- Committed the release-ready `v1.18.0` surfaces at `6e8f193` and re-ran the source-of-truth focused relaunch slice plus smoke slice from that exact commit.
- Pushed `feat/v1.18.0-relaunch-lanes` to origin at `6e8f193708cd7dd30a2d827d952e78802cbd598a`.
- Created and pushed annotated tag `v1.18.0` with tag object `7554645331a8712cd6a7f6cd0cd84dd09df8abdf`, peeling to the same shipped commit `6e8f193708cd7dd30a2d827d952e78802cbd598a`.
- Built release artifacts in `dist-release-v1.18.0/`, published them to PyPI via `twine upload`, and verified `agentkit-cli==1.18.0` live with both the wheel and sdist.
- Reconciled `BUILD-REPORT.md`, `BUILD-REPORT-v1.18.0.md`, `FINAL-SUMMARY.md`, and this progress log so later branch-head movement is explicitly documented as post-ship chronology cleanup only.

**Validation:**
- `uv run python -m pytest -q tests/test_relaunch_engine.py tests/test_resume_engine.py tests/test_reconcile_engine.py tests/test_relaunch_cmd.py tests/test_resume_cmd.py tests/test_main.py tests/test_relaunch_workflow.py tests/test_resume_workflow.py tests/test_launch_workflow.py` -> `32 passed in 32.04s`
- `uv run python -m pytest -m smoke -q --tb=short` -> `9 passed, 4958 deselected in 18.44s`
- PyPI JSON proof: `agentkit_cli-1.18.0-py3-none-any.whl` (`675725` bytes) and `agentkit_cli-1.18.0.tar.gz` (`1191256` bytes)

**Current truth:**
- D1 through D4 are complete.
- `agentkit-cli v1.18.0` is truthfully SHIPPED.
- The shipped artifact is pinned to `v1.18.0` -> `6e8f193`; any later branch-head advance is docs-only chronology reconciliation.

## D3 complete: relaunch-ready handoff packets landed

**What changed:**
- Finished the per-lane relaunch packet shape with fresh `handoff.md`, launch helper files, upstream evidence paths, and explicit review notes for stale worktrees or unresolved review lanes.
- Kept waiting, review-only, and completed lanes visible in the relaunch plan while generating fresh launch-ready packets only for `relaunch-now` lanes.
- Added end-to-end workflow coverage for `launch -> observe -> supervise -> reconcile -> resume -> relaunch` and packet writing assertions.

**Validation:**
- `python3 -m pytest -q tests/test_relaunch_engine.py tests/test_relaunch_workflow.py tests/test_resume_workflow.py tests/test_launch_workflow.py` -> `9 passed in 3.09s`

**Current truth:**
- D1 through D3 are complete.
- D4 remains in progress.
- The repo is still local-only and not yet release-ready for `v1.18.0`.

## D2 complete: first-class `agentkit relaunch` CLI landed

**What changed:**
- Added `agentkit_cli/commands/relaunch_cmd.py` and wired `agentkit relaunch` into `agentkit_cli/main.py`.
- Added deterministic CLI flows for `--json`, `--output-dir`, `--resume-path`, and `--packet-dir` so saved resume artifacts can be turned into relaunch reports and packet directories without mutating git state.
- Added focused command coverage for relaunch output writing, explicit resume directory loading, and command help surfaces.

**Validation:**
- `python3 -m pytest -q tests/test_relaunch_cmd.py tests/test_resume_cmd.py tests/test_main.py` -> `13 passed in 1.89s`

**Current truth:**
- D1 and D2 are complete.
- D3 and D4 remain in progress.
- The repo is still local-only and not yet release-ready for `v1.18.0`.

## D1 complete: schema-backed relaunch planning landed

**What changed:**
- Added `agentkit_cli/relaunch.py` with deterministic relaunch plan assembly from saved `resume.json` plus upstream `reconcile.json` and `launch.json` evidence.
- Extended `agentkit_cli/schemas.py` with `agentkit.relaunch.v1` plan and lane dataclasses so markdown and JSON outputs stay schema-backed.
- Added focused relaunch engine coverage for eligible-lane packet planning, preserved review buckets, contradiction checks for unsatisfied relaunch dependencies, and stale worktree notes.

**Validation:**
- `python3 -m pytest -q tests/test_relaunch_engine.py tests/test_resume_engine.py tests/test_reconcile_engine.py` -> `14 passed in 3.79s`

**Current truth:**
- D1 is complete.
- D2 through D4 remain in progress.
- The repo is still local-only and not yet release-ready for `v1.18.0`.
