# BUILD-REPORT-v1.18.0.md

Status: SHIPPED
Date: 2026-04-20

- Release branch on origin: `feat/v1.18.0-relaunch-lanes` -> `6e8f193708cd7dd30a2d827d952e78802cbd598a`
- Shipped annotated tag: `v1.18.0` -> tag object `7554645331a8712cd6a7f6cd0cd84dd09df8abdf`, peeled commit `6e8f193708cd7dd30a2d827d952e78802cbd598a`
- Version surfaces: `pyproject.toml`, `agentkit_cli/__init__.py`, `README.md`, and `CHANGELOG.md` target `1.18.0`
- Supported handoff lane now ends with `relaunch` after `resume`
- Validation: `uv run python -m pytest -q tests/test_relaunch_engine.py tests/test_resume_engine.py tests/test_reconcile_engine.py tests/test_relaunch_cmd.py tests/test_resume_cmd.py tests/test_main.py tests/test_relaunch_workflow.py tests/test_resume_workflow.py tests/test_launch_workflow.py` -> `32 passed in 32.04s`
- Smoke validation: `uv run python -m pytest -m smoke -q --tb=short` -> `9 passed, 4958 deselected in 18.44s`
- PyPI live: `https://pypi.org/project/agentkit-cli/1.18.0/`
- PyPI JSON proof: `agentkit_cli-1.18.0-py3-none-any.whl` (`675725` bytes), `agentkit_cli-1.18.0.tar.gz` (`1191256` bytes)
- Chronology note: shipped artifact is pinned to tag target `6e8f193`; later branch-head movement is reserved for docs-only reconciliation
- Canonical narrative: see `BUILD-REPORT.md`, `FINAL-SUMMARY.md`, and `progress-log.md`
