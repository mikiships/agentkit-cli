# BUILD-REPORT.md — agentkit-cli v1.18.0 relaunch lanes

Status: SHIPPED
Date: 2026-04-20
Contract: all-day-build-contract-agentkit-cli-v1.18.0-relaunch-lanes.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Added schema-backed relaunch planning, resume/reconcile/launch contradiction checks, per-lane eligibility metadata, and focused relaunch engine coverage |
| D2 | ✅ Complete | Added first-class `agentkit relaunch` wiring, deterministic stdout behavior, `--json`, `--output-dir`, `--resume-path`, and per-lane packet directory coverage |
| D3 | ✅ Complete | Added fresh per-lane relaunch handoff packets, helper commands, stale-worktree notes, and end-to-end `launch -> observe -> supervise -> reconcile -> resume -> relaunch` workflow coverage |
| D4 | ✅ Complete | Verified the four release surfaces, pushed the release branch, created and pushed annotated tag `v1.18.0`, published `agentkit-cli==1.18.0`, and reconciled the docs chronology after shipment |

## Validation

- Focused relaunch release slice from shipped commit `6e8f193`: `uv run python -m pytest -q tests/test_relaunch_engine.py tests/test_resume_engine.py tests/test_reconcile_engine.py tests/test_relaunch_cmd.py tests/test_resume_cmd.py tests/test_main.py tests/test_relaunch_workflow.py tests/test_resume_workflow.py tests/test_launch_workflow.py` -> `32 passed in 32.04s`
- Smoke slice in supported Python environment from shipped commit `6e8f193`: `uv run python -m pytest -m smoke -q --tb=short` -> `9 passed, 4958 deselected in 18.44s`

## Release truth

- Release branch on origin: `feat/v1.18.0-relaunch-lanes` is pushed and now carries docs-only chronology reconciliation commits after shipment
- Annotated tag on origin: `v1.18.0` -> tag object `7554645331a8712cd6a7f6cd0cd84dd09df8abdf`, peeled commit `6e8f193708cd7dd30a2d827d952e78802cbd598a`
- PyPI live: `https://pypi.org/project/agentkit-cli/1.18.0/`
- PyPI JSON proof: `agentkit_cli-1.18.0-py3-none-any.whl` (`675725` bytes) and `agentkit_cli-1.18.0.tar.gz` (`1191256` bytes)

## Chronology

- Shipped release commit: `6e8f193` (`chore: prepare v1.18.0 release surfaces`)
- Supported handoff lane target: `source -> source-audit -> map -> contract -> bundle -> taskpack -> clarify -> resolve -> dispatch -> stage -> materialize -> launch -> observe -> supervise -> reconcile -> resume -> relaunch`
- Version surfaces reflect `1.18.0`
- This report is the post-ship chronology reconciliation surface; branch head may advance after the shipped tag only for truthful release-report updates
- Canonical versioned closeout report: `BUILD-REPORT-v1.18.0.md`
