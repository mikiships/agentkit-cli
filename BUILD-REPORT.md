# BUILD-REPORT.md — agentkit-cli v1.1.0 burn observability

Date: 2026-04-19
Builder: subagent burn observability pass
Contract: all-day-build-contract-agentkit-cli-v1.1.0-burn-observability.md
Status: SHIPPED

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

- focused burn slice: `uv run pytest -q tests/test_burn_adapters.py tests/test_burn_engine.py tests/test_burn_command.py tests/test_burn_report.py` -> `24 passed in 0.44s`
- full suite baseline target retained: `>= 2623` tests
- final full suite: `uv run pytest -q` -> `4811 passed, 1 warning in 134.73s (0:02:14)`
- helper scripts: status-conflict scan `0 findings`, hygiene check `0 findings`

## Release Verification

- git branch pushed: `origin/feat/v1.1.0-burn-observability` -> `a704a0604d00737e9d024a27e67e89a92f212da3`
- annotated tag pushed: `v1.1.0` tag object `43ca8f79a139f07d8876658a514deeb9c1389aa9`, peeled commit `a704a0604d00737e9d024a27e67e89a92f212da3`
- build artifacts: `dist/agentkit_cli-1.1.0.tar.gz`, `dist/agentkit_cli-1.1.0-py3-none-any.whl`
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

SHIPPED. All four release surfaces are now confirmed directly in this pass: local tests green, release branch pushed, annotated tag `v1.1.0` pushed, and `agentkit-cli==1.1.0` live on PyPI.
