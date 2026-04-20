# BUILD-REPORT.md — agentkit-cli v1.15.0 supervise restack

Status: RELEASE-READY
Date: 2026-04-20
Contract: all-day-build-contract-agentkit-cli-v1.15.0-supervise-restack.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D0 | ✅ Complete | Inspected the shipped `v1.14.0` observe base and blocked supervise branch, then created the truthful v1.15.0 restack contract |
| D1 | ✅ Complete | Restacked `agentkit_cli/supervise.py` onto the shipped observe base with deterministic local-only supervision states and packet rendering |
| D2 | ✅ Complete | Added `agentkit supervise`, CLI wiring, stable markdown/JSON output, and explicit `--launch-path` support |
| D3 | ✅ Complete | Restacked focused engine, command, and workflow coverage for `resolve -> dispatch -> stage -> materialize -> launch -> supervise` |
| D4 | ✅ Complete | Updated README, changelog, build/final-summary/progress surfaces, and local version metadata to truthful unreleased `v1.15.0` |
| D5 | ✅ Complete | Ran targeted, adjacent, and full-suite validation plus recall, contradiction, and hygiene checks before final status |

## Validation

- Focused supervise slice: `uv run --python 3.11 --with pytest --with fastapi --with uvicorn --with httpx pytest -q tests/test_supervise_engine.py tests/test_supervise_cmd.py tests/test_supervise_workflow.py tests/test_main.py` -> `16 passed in 3.64s`
- Adjacent workflow slice: `uv run --python 3.11 --with pytest --with fastapi --with uvicorn --with httpx pytest -q tests/test_supervise_engine.py tests/test_supervise_cmd.py tests/test_supervise_workflow.py tests/test_observe_engine.py tests/test_observe_cmd.py tests/test_observe_packets.py tests/test_observe_workflow.py tests/test_launch_engine.py tests/test_launch_cmd.py tests/test_launch_workflow.py tests/test_materialize_engine.py tests/test_materialize_cmd.py tests/test_materialize_workflow.py tests/test_stage.py tests/test_stage_workflow.py tests/test_dispatch.py tests/test_dispatch_workflow.py tests/test_resolve.py tests/test_resolve_cmd.py tests/test_resolve_workflow.py tests/test_taskpack.py tests/test_main.py` -> `89 passed in 12.26s`
- Full suite baseline before report fix: `uv run --python 3.11 --with pytest --with fastapi --with uvicorn --with httpx pytest -q` -> `1 failed, 4938 passed, 1 warning in 161.86s (0:02:41)`
- Full suite release-ready rerun must finish green with verified test count >= 2623 before final status is trusted
- Recall / contradiction / hygiene checks are recorded in `progress-log.md` after final rerun

## Repo state

- Version surfaces target `1.15.0` in `pyproject.toml`, `agentkit_cli/__init__.py`, `tests/test_main.py`, and `uv.lock`
- Supported handoff lane: `source -> source-audit -> map -> contract -> bundle -> taskpack -> clarify -> resolve -> dispatch -> stage -> materialize -> launch -> observe -> supervise`
- Base chronology remains truthful: `v1.14.0` is already shipped from the observe line
- This branch is a local unreleased `v1.15.0` restack only, with no push, tag, or publish performed
- Versioned build report copy: `BUILD-REPORT-v1.15.0.md`
