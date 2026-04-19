# BUILD-REPORT.md — agentkit-cli v1.1.0 burn observability

Date: 2026-04-19
Builder: subagent burn observability pass
Contract: all-day-build-contract-agentkit-cli-v1.1.0-release.md
Status: SHIPPED, VERIFIED, AND CHRONOLOGY-RECONCILED

## Summary

Completed a local-first `agentkit burn` workflow for transcript cost observability. The release adds transcript adapters, a normalized burn schema, an analysis engine for spend and waste patterns, a first-class CLI command, and a dark-theme HTML report.

## Deliverables

| # | Deliverable | Status | Notes |
|---|-------------|--------|-------|
| D1 | Transcript adapters + normalized burn schema | ✅ Complete | Codex, Claude Code, and OpenClaw-style local artifacts normalize into one session/turn schema with explicit cost states |
| D2 | Burn analysis engine | ✅ Complete | Aggregates spend by project/model/provider/task/source and detects waste patterns with stable evidence |
| D3 | `agentkit burn` CLI command | ✅ Complete | Supports `--path`, `--format json`, `--since`, `--limit`, `--project`, and `--output` |
| D4 | HTML report + narrative summary | ✅ Complete | Dark-theme HTML and markdown-ready summary highlight where spend goes and what to fix first |
| D5 | Docs, versioning, build report, and validation | ✅ Complete | README, changelog, progress log, version metadata, helper-script checks, and local validation updated for `1.1.0` |

## Workflow Highlights

- parse local transcript artifacts with deterministic adapters
- normalize missing or estimated costs instead of guessing silently
- rank spend by project, model, provider, task label, and session source
- surface waste patterns before changing prompts or routing
- export stable JSON or a shareable local HTML report

## Validation

- focused burn slice rerun on the release-completion pass: `uv run pytest -q tests/test_burn_adapters.py tests/test_burn_engine.py tests/test_burn_command.py tests/test_burn_report.py tests/test_main.py` -> `31 passed in 0.80s`
- final full suite rerun on the same branch state: `uv run pytest -q` -> `4811 passed, 1 warning in 128.98s (0:02:08)`
- helper scripts from the workspace support repo: status-conflict scan `0 findings`, hygiene check `0 findings`

## Release Verification

- branch state now verified at `feat/v1.1.0-burn-observability` and `origin/feat/v1.1.0-burn-observability` -> `0c47a5a86b9f1cb409b8a02b578cb5abf15b4cf5`
- release tag remains the shipped annotated tag `v1.1.0` -> tag object `43ca8f79a139f07d8876658a514deeb9c1389aa9`, peeled commit `a704a0604d00737e9d024a27e67e89a92f212da3`
- chronology note: the branch moved after the release commit for report reconciliation only; PyPI `1.1.0` still matches the tagged release commit rather than the newer docs-only branch head
- build artifacts present locally include `dist/agentkit_cli-1.1.0.tar.gz` and `dist/agentkit_cli-1.1.0-py3-none-any.whl`
- PyPI live: `https://pypi.org/pypi/agentkit-cli/1.1.0/json` lists both `agentkit_cli-1.1.0.tar.gz` and `agentkit_cli-1.1.0-py3-none-any.whl`

## Version

- `pyproject.toml` -> `1.1.0`
- `agentkit_cli/__init__.py` -> `1.1.0`
- `uv.lock` -> `1.1.0`
- `BUILD-REPORT-v1.1.0.md` added as the versioned build-report copy

## Out of Scope

- cloud billing integrations
- provider-side instrumentation
- non-local transcript collection

## Status

SHIPPED and reconciled. The release itself is still `v1.1.0` on tag commit `a704a06`, PyPI is live for `agentkit-cli==1.1.0`, and the branch head is now the later docs-reconciliation commit `0c47a5a`.
