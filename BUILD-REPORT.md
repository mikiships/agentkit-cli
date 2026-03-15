# BUILD-REPORT: agentkit-cli v0.23.0 — Profiles System

**Built:** 2026-03-15
**Branch:** main
**Contract:** all-day-build-contract-agentkit-cli-v0.23.0-profiles.md

---

## v0.23.0 Deliverable Status

| # | Deliverable | Status |
|---|---|---|
| D1 | `agentkit_cli/profiles.py` — ProfileDefinition, ProfileRegistry, built-in presets, apply_profile | ✅ Complete |
| D1 | Three built-in presets: strict, balanced, minimal | ✅ Complete |
| D1 | User-defined profiles from `~/.agentkit/profiles/*.toml` | ✅ Complete |
| D1 | Case-insensitive profile lookup | ✅ Complete |
| D1 | apply_profile() with CLI flag precedence | ✅ Complete |
| D1 | `tests/test_profiles.py` — 40 tests | ✅ Complete |
| D2 | `agentkit profile list/show/create/use/export` | ✅ Complete |
| D2 | Wire into main.py as `agentkit profile` | ✅ Complete |
| D2 | `tests/test_profile_command.py` — 19 tests | ✅ Complete |
| D3 | `--profile` flag added to gate, run, sweep, score, analyze | ✅ Complete |
| D3 | Profile name shown in gate output | ✅ Complete |
| D3 | `tests/test_profile_integration.py` — 16 tests | ✅ Complete |
| D4 | README Profiles section | ✅ Complete |
| D4 | CHANGELOG v0.23.0 entry | ✅ Complete |
| D4 | Version bumped to 0.23.0 | ✅ Complete |
| D4 | All tests pass (891 passing) | ✅ Complete |

---

# BUILD-REPORT: agentkit-cli v0.22.0 — Config System

**Built:** 2026-03-15  
**Branch:** main  
**Contract:** memory/contracts/agentkit-cli-v0.22.0-config.md

---

## Deliverable Status

| # | Deliverable | Status |
|---|---|---|
| D1 | `agentkit_cli/config.py` — TOML config loading with git-style traversal, user config, env vars, `AgentKitConfig` dataclass | ✅ Complete |
| D1 | `.agentkit.toml` traversal from cwd upward | ✅ Complete |
| D1 | `~/.config/agentkit/config.toml` user-level defaults | ✅ Complete |
| D1 | Environment variable overrides (12 vars) | ✅ Complete |
| D1 | Config precedence: CLI > env > project > user > defaults | ✅ Complete |
| D1 | `tomllib` (Python 3.11+) with `tomli` fallback | ✅ Complete |
| D1 | Graceful error on invalid TOML | ✅ Complete |
| D2 | Wire config into `agentkit gate` | ✅ Complete |
| D2 | Wire config into `agentkit run` | ✅ Complete |
| D2 | Wire config into `agentkit sweep` | ✅ Complete |
| D2 | Wire config into `agentkit score` | ✅ Complete |
| D2 | Wire config into `agentkit notify` (via gate/run) | ✅ Complete |
| D2 | Wire config into `agentkit analyze` | ✅ Complete (via gate/run) |
| D3 | `agentkit config init` | ✅ Complete |
| D3 | `agentkit config init --global` | ✅ Complete |
| D3 | `agentkit config show` (with source annotations) | ✅ Complete |
| D3 | `agentkit config show --json` | ✅ Complete |
| D3 | `agentkit config get <key>` | ✅ Complete |
| D3 | `agentkit config set <key> <value>` | ✅ Complete |
| D3 | `--global` flag on init/set/get | ✅ Complete |
| D4 | 58 new tests in `tests/test_config.py` (target: 30+) | ✅ Complete (58 tests) |
| D4 | Tests: loading, precedence, env var overrides | ✅ Complete |
| D4 | Tests: init/show/set/get CLI | ✅ Complete |
| D4 | README "Project Configuration" section | ✅ Complete |
| D4 | CHANGELOG entry for v0.22.0 | ✅ Complete |
| D4 | Version bump to 0.22.0 in pyproject.toml | ✅ Complete |
| D4 | Version bump to 0.22.0 in `agentkit_cli/__init__.py` | ✅ Complete |

---

## Test Results

```
817 passed, 1 pre-existing failure (test_watch.py::TestChangeHandler::test_last_file_recorded — IndexError, pre-existing, not introduced by this build)
```

New tests in `tests/test_config.py`: **58 passing**

---

## Key Design Decisions

- Used `tomllib` (stdlib) with no new hard dependencies. `tomli` fallback for older Pythons.
- Minimal TOML writer (`_dict_to_toml`) avoids adding `tomli-w` dependency.
- Source tracking via `_sources` dict on `AgentKitConfig` enables `config show` source annotations.
- Legacy `.agentkit.yaml` system preserved fully for backward compat.
- Config wired via "apply defaults when flag is None" pattern — no breaking changes to CLI interface.
