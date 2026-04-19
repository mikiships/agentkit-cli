# BUILD-REPORT.md — agentkit-cli v1.0.0 canonical source workflow

Date: 2026-04-19
Builder: subagent canonical source pass
Contract: all-day-build-contract-agentkit-cli-v1.0.0-canonical-source-kit.md
Status: Complete, fully validated locally

## Summary

Completed the dedicated canonical source workflow that complements the v0.99.0 projection release. agentkit now has one explicit agentkit-managed source file at `.agentkit/source.md`, a bootstrap/promote command for adopting it, and native project/init/sync behavior that respects it end to end.

## Deliverables

| # | Deliverable | Status | Notes |
|---|-------------|--------|-------|
| D1 | Dedicated canonical source path + engine support | ✅ Complete | `.agentkit/source.md` added as the preferred canonical source with backwards-compatible legacy detection fallback |
| D2 | Bootstrap/promote command | ✅ Complete | `agentkit source` can initialize a fresh template or promote an existing legacy context file deterministically |
| D3 | Projection/init/sync integration | ✅ Complete | `project`, `sync`, and `init` now all respect the dedicated source workflow |
| D4 | Docs, reports, versioning, and final validation | ✅ Complete | README, changelog, build report, progress log, version metadata, and validation all reconciled for `1.0.0` |

## Workflow Highlights

- dedicated authoring path: `.agentkit/source.md`
- create a fresh source: `agentkit source --init`
- promote an existing context file: `agentkit source --promote`
- project root files from the dedicated source: `agentkit project --targets all --write`
- drift-check or repair projections: `agentkit sync --check` / `agentkit sync --fix`
- adopt the workflow during setup: `agentkit init --init-source ...` or `agentkit init --promote-source ...`

## Validation

- targeted source workflow coverage: `uv run pytest -q tests/test_context_projections.py tests/test_source_cmd.py tests/test_project_cmd.py tests/test_sync_projections.py tests/test_init_projections.py tests/test_init.py` -> `37 passed in 1.10s`
- final full suite: `uv run pytest -q` -> `4787 passed, 1 warning in 213.80s (0:03:33)`

## Version

- `pyproject.toml` -> `1.0.0`
- `agentkit_cli/__init__.py` -> `1.0.0`
- `BUILD-REPORT-v1.0.0.md` added as the versioned build-report copy

## Status

Feature-complete locally, fully validated in-repo, not pushed or published by this pass.
