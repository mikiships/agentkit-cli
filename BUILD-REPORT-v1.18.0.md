# BUILD-REPORT-v1.18.0.md

Status: LOCAL RELEASE-READY
Date: 2026-04-20

- Branch: `feat/v1.18.0-relaunch-lanes`
- Scope: deterministic `resume -> relaunch` continuation with fresh relaunch-ready packets for eligible lanes and explicit preservation of `waiting`, `review-only`, and `completed` lanes
- Version surfaces: `pyproject.toml`, `agentkit_cli/__init__.py`, `README.md`, `CHANGELOG.md`, and `uv.lock` all target `1.18.0`
- Focused validation: `uv run python -m pytest -q tests/test_relaunch_engine.py tests/test_resume_engine.py tests/test_reconcile_engine.py tests/test_relaunch_cmd.py tests/test_resume_cmd.py tests/test_main.py tests/test_relaunch_workflow.py tests/test_resume_workflow.py tests/test_launch_workflow.py` -> `32 passed in 13.60s`
- Smoke validation: `uv run python -m pytest -m smoke -q --tb=short` -> `9 passed, 4958 deselected in 10.87s`
- Full suite: `uv run python -m pytest -q tests` -> `4967 passed, 1 warning in 434.55s (0:07:14)`
- Canonical narrative: see `BUILD-REPORT.md`, `FINAL-SUMMARY.md`, and `progress-log.md`
- Scope note: local-only closeout, unpushed, untagged, unpublished
