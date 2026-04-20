# BUILD-REPORT.md — agentkit-cli v1.12.0 materialize worktrees

Status: SHIPPED
Date: 2026-04-20
Contract: all-day-build-contract-agentkit-cli-v1.12.0-release.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Added `agentkit_cli/materialize.py` with deterministic local worktree planning from saved stage artifacts |
| D2 | ✅ Complete | Added `agentkit materialize`, stable markdown and JSON output, `--dry-run`, and real local `git worktree add` execution |
| D3 | ✅ Complete | Added seeded `.agentkit/materialize/` handoff packets with copied stage artifacts, metadata, and target-aware notes |
| D4 | ✅ Complete | Added regression coverage for `resolve -> dispatch -> stage -> materialize`, serialized lanes, collision safety, and deterministic worktree creation |
| D5 | ✅ Complete | Pushed branch and tag, published `agentkit-cli==1.12.0`, and reconciled shipped release surfaces |

## Validation

- Focused materialize slice on the shipped release line: `python3 -m pytest -q tests/test_materialize_engine.py tests/test_materialize_cmd.py tests/test_materialize_workflow.py` -> `9 passed in 2.31s`
- Cross-lane workflow slice on the shipped release line: `python3 -m pytest -q tests/test_materialize_engine.py tests/test_materialize_cmd.py tests/test_materialize_workflow.py tests/test_stage.py tests/test_stage_workflow.py tests/test_dispatch.py tests/test_dispatch_workflow.py tests/test_resolve.py tests/test_resolve_workflow.py tests/test_resolve_cmd.py tests/test_taskpack.py` -> `46 passed in 4.04s`
- CLI integration slice on the shipped release line: `python3 -m pytest -q tests/test_main.py tests/test_materialize_engine.py tests/test_materialize_cmd.py tests/test_materialize_workflow.py` -> `16 passed in 2.64s`
- Release recall: `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.12.0-materialize-worktrees` -> completed before trusting release surfaces in this pass
- Contradiction scan: `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.12.0-materialize-worktrees` -> no contradictory success or blocker narratives found
- Full suite on the shipped release line: `.venv/bin/python -m pytest tests/ -x` -> `4903 passed, 1 warning in 417.24s (0:06:57)` for tested release commit `9e1e1440f01e557857c84b4ac00a405f3e51f505`
- Git push verification: `git ls-remote --heads origin feat/v1.12.0-materialize-worktrees` -> branch pushed and later allowed to advance only through docs-only chronology cleanup after the shipped tag
- Tag verification: `git ls-remote --tags origin refs/tags/v1.12.0^{}` -> shipped release commit `9e1e1440f01e557857c84b4ac00a405f3e51f505`
- Registry build and publish: `uv build .release-build/v1.12.0-from-tag --out-dir dist --sdist --wheel`, `uv run --with twine python -m twine check dist/agentkit_cli-1.12.0.tar.gz dist/agentkit_cli-1.12.0-py3-none-any.whl`, and `uv run --with twine python -m twine upload dist/agentkit_cli-1.12.0.tar.gz dist/agentkit_cli-1.12.0-py3-none-any.whl` -> success
- Registry verification: `https://pypi.org/pypi/agentkit-cli/1.12.0/json` -> `1.12.0` live with `agentkit_cli-1.12.0.tar.gz` and `agentkit_cli-1.12.0-py3-none-any.whl`

## Repo state

- Version surfaces target `1.12.0` in `pyproject.toml`, `agentkit_cli/__init__.py`, and `tests/test_main.py`
- The supported handoff lane is `source -> source-audit -> map -> contract -> bundle -> taskpack -> clarify -> resolve -> dispatch -> stage -> materialize`
- Shipped release commit: `9e1e1440f01e557857c84b4ac00a405f3e51f505`
- Annotated tag: `v1.12.0` -> `9e1e1440f01e557857c84b4ac00a405f3e51f505`
- PyPI: `https://pypi.org/project/agentkit-cli/1.12.0/`
- Any later branch movement after the tag is docs-only chronology cleanup, not a new shipped artifact
