# BUILD-REPORT.md — agentkit-cli v1.29.0 flagship self-advance

Status: IN PROGRESS
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.29.0-release.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Re-verified current-tree source, current branch/head state, focused tests, full suite, and reconciled the stale local-ready mismatch by restoring the package version surfaces to `1.29.0`. |
| D2 | ⏳ In Progress | Branch push, annotated tag creation, and remote ref proof pending. |
| D3 | ⏳ In Progress | Fresh `1.29.0` artifacts, PyPI publish, and registry proof pending. |
| D4 | ⏳ In Progress | Final chronology reconciliation, contradiction scan, hygiene scan, and clean-tree closeout pending. |

## Validation

- `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.29.0-flagship-self-advance` -> recall run completed; surfaced active release cues and reminded that all four release surfaces must be proven directly.
- `git status --short --branch` -> branch `feat/v1.29.0-flagship-self-advance`; current tree initially showed the release contract file untracked.
- `git rev-parse HEAD` -> current local release-candidate head started at `f96cd44941a0cbb96c7e212b0cebbc82009cd707` before release-completion edits.
- `python -m agentkit_cli.main source-audit . --json` -> `ready_for_contract=true`, `findings=[]`.
- `python -m agentkit_cli.main spec . --json` -> `kind=flagship-adjacent-next-step`; objective advanced past the closed `flagship-post-closeout-advance` lane.
- `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `29 passed in 1.79s`.
- `uv run python -m pytest -q` -> `5017 passed, 1 warning in 190.05s (0:03:10)`.
- Source-of-truth mismatch found during release verification: `pyproject.toml` and `agentkit_cli/__init__.py` still reported `1.28.0` even though the repo was carrying the `v1.29.0` lane. Reconciled those version surfaces before proceeding with branch/tag/publish work.

## Current truth

- The local-ready claim was not yet release-truthful at start because package version surfaces still said `1.28.0`; that mismatch is now reconciled in-tree.
- Release-critical validation from the current tree is green: focused slice `29 passed in 1.79s`, full suite `5017 passed, 1 warning in 190.05s (0:03:10)`.
- The live planner result remains the intended shipped behavior for this lane: `flagship-adjacent-next-step` / `Emit the next flagship lane after post-closeout advance`.
- Branch push, annotated tag `v1.29.0`, PyPI publish, and final shipped chronology proof are still pending in this report.
