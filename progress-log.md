# Progress Log — agentkit-cli v1.29.0 flagship self-advance

Status: SHIPPED
Date: 2026-04-21

## Why this lane exists

After `v1.28.0` shipped, the flagship repo still let `agentkit spec . --json` replay `flagship-post-closeout-advance` from its own shipped truth. The planner advanced one lane, but not past itself.

## Current starting truth

- Branch head inherited from shipped chronology surface: `47ab71e`
- `v1.28.0` is already shipped, with annotated tag and PyPI live
- Shipped workflow artifacts already close `flagship-post-closeout-advance`: `CHANGELOG.md` `1.28.0`, `BUILD-REPORT.md` status `SHIPPED`, and `FINAL-SUMMARY.md` status `SHIPPED`
- Before the fix, the live planner fell through to generic `subsystem-next-step` even though repo truth had already finished the post-closeout lane and needed one more flagship-specific advance

## Deliverable progress

### D1. Reproduce and ground the stale planner state
- Proved shipped truth from current repo artifacts: `CHANGELOG.md` `1.28.0`, `BUILD-REPORT.md` `Status: SHIPPED`, `FINAL-SUMMARY.md` `Status: SHIPPED`
- Proved the old planner gap from current tree: `python3 -m agentkit_cli.main spec . --json` returned `subsystem-next-step` instead of a fresh flagship lane
- Locked the suppression evidence pattern to shipped or truthful local-release-ready workflow artifacts that explicitly mention `flagship-post-closeout-advance`

### D2. Advance the flagship recommendation logic
- Added deterministic post-closeout closeout detection in `agentkit_cli/spec_engine.py`
- Promoted `flagship-adjacent-next-step` as the fresh adjacent flagship recommendation and contract seed
- Added focused regressions across spec engine, command, and workflow paths for the post-closeout case
- Deliverable-cluster commit: `6529650` (`fix: advance flagship planner past post-closeout lane`)

### D3. Truthful local planning-surface refresh
- Refreshed `.agentkit/source.md` so the active objective names `flagship-adjacent-next-step`
- Refreshed `BUILD-TASKS.md` to capture the actual stale-fallback reproduction and the new flagship lane truth
- Confirmed the live planner now returns `flagship-adjacent-next-step` with title `Emit the next flagship lane after post-closeout advance`
- Deliverable-cluster commit: `f96cd44` (`docs: close out v1.29.0 flagship self-advance`)

### D4. Release-completion verification and reconciliation
- Ran `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.29.0-flagship-self-advance` before trusting the release narrative
- Verified current branch and head directly: `feat/v1.29.0-flagship-self-advance` at `f96cd44941a0cbb96c7e212b0cebbc82009cd707`
- Re-ran current-tree validation: `python -m agentkit_cli.main source-audit . --json` -> ready, `python -m agentkit_cli.main spec . --json` -> `flagship-adjacent-next-step`, focused tests `29 passed in 1.79s`, full suite `5017 passed, 1 warning in 190.05s (0:03:10)`
- Found and reconciled the release-blocking source-of-truth mismatch: `pyproject.toml` and `agentkit_cli/__init__.py` still declared `1.28.0`, so `v1.29.0` was not yet publishable truthfully until those version surfaces were updated
- Refreshed `CHANGELOG.md`, `BUILD-REPORT.md`, and `FINAL-SUMMARY.md` to truthful `v1.29.0` release-in-progress state before push/tag/publish

## Validation status

- Focused regressions from the release tree: `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `29 passed in 1.79s`
- Full suite from the release tree: `uv run python -m pytest -q` -> `5017 passed, 1 warning in 190.05s (0:03:10)`

## Current release truth

- The intended shipped behavior for `v1.29.0` is still correct in the current tree: `agentkit spec . --json` advances to `flagship-adjacent-next-step`
- Release verification started by catching a real blocker, package version surfaces still on `1.28.0`, and reconciled that mismatch before any git or registry mutation
- Branch `feat/v1.29.0-flagship-self-advance` is live on origin and annotated tag `v1.29.0` now points at the shipped release commit
- PyPI now serves `agentkit-cli==1.29.0` with `agentkit_cli-1.29.0-py3-none-any.whl` and `agentkit_cli-1.29.0.tar.gz`
- Contradiction scan and hygiene scan both closed cleanly
