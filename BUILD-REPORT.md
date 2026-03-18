# agentkit-cli v0.49.0 — Build Report

**Build date:** 2026-03-18
**Version:** 0.49.0 (bumped from 0.48.0)

## Deliverables Status

| # | Deliverable | Status | Notes |
|---|---|---|---|
| D1 | GitHubChecksClient core API client | ✅ DONE | 18 tests |
| D2 | CheckRun output formatter | ✅ DONE | 21 tests |
| D3 | Integration with `agentkit run` and `agentkit gate` | ✅ DONE | 12 tests |
| D4 | `agentkit checks` CLI command (verify/post/status) | ✅ DONE | 12 tests |
| D5 | Docs, CHANGELOG, version bump, BUILD-REPORT | ✅ DONE | — |

## Test Count Delta

| Metric | Value |
|---|---|
| Baseline | 2138 |
| New tests added | 63 (D1: 18, D2: 21, D3: 12, D4: 12) |
| Final count | ≥2183 |
| Suite result | ✅ 0 failures |

## New Files

```
agentkit_cli/checks_client.py       — GitHubChecksClient (create/update check runs via REST API)
agentkit_cli/checks_formatter.py    — format_check_output() (score → Check Run markdown + annotations)
agentkit_cli/commands/checks_cmd.py — checks_app: verify / post / status subcommands
tests/test_checks_client.py
tests/test_checks_formatter.py
tests/test_checks_integration.py
tests/test_checks_cmd.py
```

## Modified Files

```
agentkit_cli/main.py               — registered checks_app typer group, added --checks flag to run/gate
agentkit_cli/commands/run_cmd.py    — added checks lifecycle (create on start, update on complete)
agentkit_cli/commands/gate_cmd.py   — added checks lifecycle with pass/fail conclusion mapping
agentkit_cli/commands/ci.py         — added checks: write permission to workflow template
agentkit_cli/__init__.py            — bumped __version__ to 0.49.0
pyproject.toml                      — bumped version to 0.49.0
CHANGELOG.md                        — added v0.49.0 entry
README.md                           — added "GitHub Checks API" section
tests/test_explain.py               — updated version assertions to 0.49.0
tests/test_improve.py               — updated version assertions to 0.49.0
tests/test_monitor_d5.py            — updated version assertions to 0.49.0
tests/test_timeline_d5.py           — updated version assertions to 0.49.0
tests/test_certify_d5.py            — updated version assertions to 0.49.0
```

## Validation Gates

| Gate | Status |
|---|---|
| `python3 -m pytest -q` ≥2120 tests, 0 failures | ✅ |
| `agentkit checks --help` shows verify/post/status | ✅ |
| `agentkit checks verify` reports env var status | ✅ |
| `agentkit run --help` shows --checks/--no-checks | ✅ |
| `agentkit gate --help` shows --checks/--no-checks | ✅ |
| CI template includes `checks: write` permission | ✅ |
| `grep -r "0.48.0" pyproject.toml` returns nothing | ✅ |
| Git log shows 5 commits (one per deliverable) | ✅ D1–D5 committed |
