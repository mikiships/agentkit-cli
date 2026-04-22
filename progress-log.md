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
- Verified current-tree release truth directly: `python -m agentkit_cli.main source-audit . --json` -> ready, `python -m agentkit_cli.main spec . --json` -> `flagship-adjacent-next-step`, focused tests `29 passed in 1.83s`, full suite `5017 passed, 1 warning in 190.83s (0:03:10)`
- Found and reconciled the real release blocker before shipping: `pyproject.toml` and `agentkit_cli/__init__.py` still declared `1.28.0`, and `tests/test_main.py` still expected `1.28.0`
- Deliverable-cluster commits: `2c71ab1` (`docs: start v1.29.0 release completion`) and `404ada0` (`test: update version assertion for v1.29.0`)
- Verified remote branch directly: `origin/feat/v1.29.0-flagship-self-advance` exists and remains ahead with docs-only closeout commits
- Verified and reconciled annotated tag truth directly: `v1.29.0` had initially peeled to `c80e636d41d6a38437792fd35131889ca44d0831`, which predated the version-assertion test fix, so the annotated tag was corrected and force-pushed; it now peels to shipped commit `404ada0eb6cf8092659d567b10f3c28448aafc66`
- Verified release artifacts and registry directly: `dist/agentkit_cli-1.29.0-py3-none-any.whl`, `dist/agentkit_cli-1.29.0.tar.gz`, PyPI project JSON `info.version=1.29.0`, and PyPI version JSON files `agentkit_cli-1.29.0-py3-none-any.whl` plus `agentkit_cli-1.29.0.tar.gz`
- Final contradiction scan: `No contradictory success/blocker narratives found.`
- Final hygiene scan: `Total findings: 0`

## Validation status

- Focused regressions from the shipped release tree: `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `29 passed in 1.83s`
- Full suite from the shipped release tree: `uv run python -m pytest -q` -> `5017 passed, 1 warning in 190.83s (0:03:10)`

## Final shipped truth

- Shipped release commit: `404ada0eb6cf8092659d567b10f3c28448aafc66`
- Later docs-only chronology: additional closeout commits on `origin/feat/v1.29.0-flagship-self-advance`
- Remote branch ref: `origin/feat/v1.29.0-flagship-self-advance`
- Annotated tag object: `1eb19058143ef3f6629e6f25da6041f0213efbeb`
- Tag peel: `404ada0eb6cf8092659d567b10f3c28448aafc66`
- PyPI live: `agentkit-cli==1.29.0` with `agentkit_cli-1.29.0-py3-none-any.whl` and `agentkit_cli-1.29.0.tar.gz`
- Shipped functional outcome: `agentkit spec . --json` advances to `flagship-adjacent-next-step`
