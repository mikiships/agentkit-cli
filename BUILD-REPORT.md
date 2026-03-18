# BUILD-REPORT — agentkit-cli v0.47.0

**Date:** 2026-03-18
**Version:** 0.47.0
**Baseline tests:** 1969 (v0.46.0)
**Target tests:** ≥2021
**Build:** agentkit monitor — Continuous Quality Monitoring Daemon

---

## Deliverable Status

| Deliverable | Status | Tests |
|---|---|---|
| D1: MonitorConfig + persistence layer | ✅ COMPLETE | 29 |
| D2: MonitorEngine + daemon runner | ✅ COMPLETE | 21 |
| D3: `agentkit monitor` CLI command | ✅ COMPLETE | 24 |
| D4: Daemon background process | ✅ COMPLETE | 9 |
| D5: Docs, CHANGELOG, version bump | ✅ COMPLETE | 10 |

**Total new tests:** 93
**Final test count:** 2062 passing

---

## D1: MonitorConfig + Persistence Layer

- `agentkit_cli/monitor_config.py`
- `MonitorTarget` dataclass with all fields (schedule, notify URLs, thresholds, last run state)
- `MonitorConfig` class: load/save from `.agentkit.toml` `[monitor.targets]` section
- Preserves other TOML sections on save (gate, notify, run, sweep, score)
- `add_target()`, `remove_target()`, `list_targets()`, `get_target()`, `update_last_run()`
- TOML serializer handles special chars in keys (`:`, `/` in target names)
- Tests: `tests/test_monitor_config.py` (29 tests)

## D2: MonitorEngine + Daemon Runner

- `agentkit_cli/monitor_engine.py`
- `MonitorResult` dataclass: target, score, prev_score, delta, timestamp, notify_fired, error
- `check_target()`: runs analyze fn, computes delta vs prev_score
- `should_notify()`: fires when abs(delta) >= alert_threshold OR score drops below min_score
- `run_check()`: check + notify + config update in one call
- `run_all_due()`: filters targets by schedule period, runs due ones
- `run_target()`: force-run specific target
- Tests: `tests/test_monitor_engine.py` (21 tests, mocked ToolAdapter)

## D3: `agentkit monitor` CLI Command

- `agentkit_cli/commands/monitor.py` — Typer app with all subcommands
- Wired into `agentkit_cli/main.py` as `app.add_typer(monitor_app, name="monitor")`
- `add`: validate, add to config, confirm with options summary
- `remove`: confirm removal (--yes to skip)
- `list`: Rich table with target, schedule, last score, last checked, next due, notify ✓/✗; --json output
- `run`: all due or --target specific; Rich results table; --json output
- `start`: Popen daemon with stdout/stderr to log file, write PID file
- `stop`: read PID file, send SIGTERM
- `status`: daemon running/stopped + next scheduled run times; --json output
- `logs`: tail structured JSON log, render Rich table; --json output
- Tests: `tests/test_monitor_cmd.py` (24 tests)

## D4: Daemon Background Process

- `agentkit_cli/monitor_daemon.py`
- Entry point: `python -m agentkit_cli.monitor_daemon`
- Polling loop: every 60s, call `run_all_due()`, sleep remainder
- SIGTERM handler: sets `_running = False`, logs shutdown event
- Structured JSON log: `{"ts", "target", "score", "prev_score", "delta", "notify_fired", "error"}`
- Startup/exit/error events also logged as JSON
- `~/.agentkit/` directory created if not exists
- `_test_max_cycles` param for deterministic unit testing
- Tests: `tests/test_monitor_daemon.py` (9 tests, incl. subprocess integration)

## D5: Docs, CHANGELOG, Version Bump

- `README.md`: `agentkit monitor` section with all subcommand examples, schedule/notification docs
- `CHANGELOG.md`: v0.47.0 entry with full feature list
- `agentkit_cli/__init__.py`: `__version__ = "0.47.0"`
- `pyproject.toml`: `version = "0.47.0"`
- Fixed pre-existing version tests in test_timeline_d5.py, test_certify_d5.py, test_explain.py, test_improve.py
- Tests: `tests/test_monitor_d5.py` (10 tests)

---

## Files Modified/Created

### New Files
- `agentkit_cli/monitor_config.py`
- `agentkit_cli/monitor_engine.py`
- `agentkit_cli/commands/monitor.py`
- `agentkit_cli/monitor_daemon.py`
- `tests/test_monitor_config.py`
- `tests/test_monitor_engine.py`
- `tests/test_monitor_cmd.py`
- `tests/test_monitor_daemon.py`
- `tests/test_monitor_d5.py`

### Modified Files
- `agentkit_cli/main.py` — added `monitor_app` import and `app.add_typer`
- `agentkit_cli/__init__.py` — version 0.47.0
- `pyproject.toml` — version 0.47.0
- `CHANGELOG.md` — v0.47.0 entry
- `README.md` — monitor section
- `BUILD-REPORT.md` — this file
- `tests/test_timeline_d5.py` — version updated
- `tests/test_certify_d5.py` — version updated
- `tests/test_explain.py` — version updated
- `tests/test_improve.py` — version updated
