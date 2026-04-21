# Progress Log — agentkit-cli v1.27.0 spec concrete next step

Status: RELEASE-READY (LOCAL-ONLY)
Date: 2026-04-21

## Why this lane exists

After the v1.26.0 shipped-truth-sync closeout, the flagship repo still let `agentkit spec . --json` fall through to the generic `subsystem-next-step` recommendation. That left the self-spec flow truthful about shipped history, but still not concrete enough to open the next flagship lane without manual reinterpretation.

## Root cause

`agentkit_cli/spec_engine.py` already had a higher-priority `flagship-concrete-next-step` rule, but its trigger still required the older demo-fixture objective phrases `self-spec truthful` and `shipped repo evidence`. The real flagship `.agentkit/source.md` objective had already moved to the newer `Teach the flagship self-spec flow...` wording, so the live command path never matched the flagship rule and fell through to the generic subsystem fallback.

## What changed

- Tightened the existing `flagship-concrete-next-step` trigger in `agentkit_cli/spec_engine.py` so it accepts the current flagship objective wording instead of only the older demo-fixture phrasing.
- Expanded workflow-artifact evidence capture enough for the planner to see the shipped-truth-sync closeout text already recorded in the local flagship reports.
- Updated focused engine, command, and workflow regressions to use the same flagship objective wording as the real repo, so this false-green case cannot recur.
- Updated local closeout surfaces so they describe the active `v1.27.0 spec concrete next step` lane truthfully.

## Validation

- `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `23 passed in 2.63s`
- `uv run python -m agentkit_cli.main spec . --json` -> `kind=flagship-concrete-next-step`; title `Emit a concrete next flagship lane after shipped-truth sync`; contract seed title `All-Day Build Contract: agentkit-cli-v1.27.0-spec-concrete-next-step spec concrete next step`
- `uv run python -m pytest -q` -> `5011 passed, 1 warning in 824.00s (0:13:44)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.27.0-spec-concrete-next-step` -> `No contradictory success/blocker narratives found.`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.27.0-spec-concrete-next-step` -> `Total findings: 0`

## Local closeout truth

This tree is truthfully `RELEASE-READY (LOCAL-ONLY)`: the focused suite passed, the flagship command path now emits `flagship-concrete-next-step`, the full pytest suite passed from this tree, the contradiction scan was clean, and the hygiene check reported `Total findings: 0`.

## 2026-04-21 full-suite closeout note

- The first full-suite pass exposed one environment-sensitive config failure caused by the repo-local `.agentkit.toml` and four report assertions caused by missing version/test-count details in `BUILD-REPORT.md`, not by the new spec planner logic.
- Removed the repo-local `.agentkit.toml` so `tests/test_config.py::TestConfigInitCLI::test_init_creates_toml` no longer saw a pre-existing config at repo root.
- Updated `BUILD-REPORT.md` to state the truthful baseline clearly: this local `v1.27.0` lane sits on shipped package version `agentkit-cli v1.26.0` and includes a verified 4-digit test-count floor.
- Re-ran the full suite once more and it closed cleanly at `5011 passed, 1 warning`.
- Final contradiction scan passed with `No contradictory success/blocker narratives found.`
- Final hygiene scan passed with `Total findings: 0`.

## 2026-04-21 release-completion pass

- Ran `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.27.0-spec-concrete-next-step` and confirmed the active build is `agentkit-cli v1.27.0 release completion`, `last_shipped` is still `v1.26.0`, and `pending_publish` is `agentkit-cli v1.27.0`.
- Ran `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.27.0-spec-concrete-next-step` before irreversible work; it reported `No contradictory success/blocker narratives found.`
- Re-ran the focused release slice: `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `23 passed in 10.85s`.
- Re-proved the flagship command path from this release tree: `uv run python -m agentkit_cli.main spec . --json` now exposes `primary_recommendation.kind = flagship-concrete-next-step`, title `Emit a concrete next flagship lane after shipped-truth sync`, and contract seed title `All-Day Build Contract: agentkit-cli-v1.27.0-spec-concrete-next-step spec concrete next step`.
- The first full-suite rerun exposed one remaining release-consistency gap: `CHANGELOG.md` still started at `v1.26.0`, so changelog/version assertions failed even though the flagship command path and focused release slice were already green.
- Added the missing `v1.27.0` changelog entry, then re-ran the affected release-consistency test cluster and it passed cleanly.
- Re-ran the full suite from this tree after the changelog fix: `uv run python -m pytest -q` -> `5011 passed, 1 warning in 1030.73s (0:17:10)`.
- Re-ran deterministic hygiene after the fix: `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.27.0-spec-concrete-next-step` -> `Total findings: 0`.
- Validation is now back to truthful `RELEASE-READY` for the irreversible release surfaces: push branch, create/push tag `v1.27.0`, publish `agentkit-cli==1.27.0`, then verify PyPI live truth.
