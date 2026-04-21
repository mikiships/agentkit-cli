# BUILD-REPORT-v1.18.0.md

Status: LOCAL RELEASE-READY
Date: 2026-04-20

- Branch: `feat/v1.18.0-relaunch-lanes`
- Local head for this closeout: `18eea61` (`test: cover relaunch workflow packets`)
- Version surfaces: `pyproject.toml`, `agentkit_cli/__init__.py`, `README.md`, and `CHANGELOG.md` all target `1.18.0`
- Supported handoff lane now ends with `relaunch` after `resume`
- Validation: `uv run python -m pytest -q tests/test_relaunch_engine.py tests/test_resume_engine.py tests/test_reconcile_engine.py tests/test_relaunch_cmd.py tests/test_resume_cmd.py tests/test_main.py tests/test_relaunch_workflow.py tests/test_resume_workflow.py tests/test_launch_workflow.py` -> `32 passed in 8.57s`
- Smoke validation: `uv run python -m pytest -m smoke -q --tb=short` -> `9 passed, 4958 deselected in 8.78s`
- Canonical narrative: see `BUILD-REPORT.md`, `FINAL-SUMMARY.md`, and `progress-log.md`
- Scope note: local-only closeout, unpushed, untagged, unpublished
