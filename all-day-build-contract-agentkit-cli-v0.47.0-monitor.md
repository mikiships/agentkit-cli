# All-Day Build Contract: agentkit monitor — Continuous Quality Monitoring Daemon

Status: In Progress
Date: 2026-03-18
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentkit monitor` — a persistent background daemon that watches configured repos on a schedule, stores results in the existing history DB, and sends notifications when quality scores change significantly.

This transforms agentkit-cli from a one-shot check tool into a continuous quality monitoring system. Target use case: "set up monitoring for 3 repos, get Slack alerts when any score drops more than 10 points."

Commands:
- `agentkit monitor add <target> [--schedule daily|weekly] [--notify-slack URL] [--notify-discord URL] [--min-score N]`
- `agentkit monitor remove <target>`
- `agentkit monitor list` — show all monitored repos with last score + schedule
- `agentkit monitor run [--target <t>]` — force an immediate check (all or specific)
- `agentkit monitor start` — start background daemon (writes PID file, polls on schedule)
- `agentkit monitor stop` — stop daemon
- `agentkit monitor status` — show daemon state + next run times
- `agentkit monitor logs [--limit N]` — recent check history from DB

Integration:
- `agentkit monitor` stores targets in `.agentkit.toml` under `[monitor]` section
- Each run writes to history DB (reuses existing HistoryDB)
- On significant score change (drop ≥10 or configurable `--alert-threshold`): fires notification via existing NotificationEngine (from v0.21.0)
- HTML report for `monitor run` reuses existing report templates

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.
11. The daemon implementation MUST be simple: no external scheduler dependencies. Use stdlib (sched, threading, or simple sleep loop in a subprocess). Do not add new deps unless absolutely necessary.
12. Daemon PID file: `~/.agentkit/monitor.pid`. Log file: `~/.agentkit/monitor.log`.

## 3. Feature Deliverables

### D1. MonitorConfig + persistence layer (≥12 tests)

Build `agentkit_cli/monitor_config.py`:
- `MonitorTarget` dataclass: target (str), schedule ("daily"/"weekly"/"hourly"), notify_slack (Optional[str]), notify_discord (Optional[str]), notify_webhook (Optional[str]), min_score (Optional[float]), alert_threshold (float, default 10.0), last_checked (Optional[str]), last_score (Optional[float])
- `MonitorConfig` class: load/save from `.agentkit.toml` `[monitor.targets]` section
- `add_target()`, `remove_target()`, `list_targets()`, `update_last_run()` methods
- Use existing `ConfigManager` from `agentkit_cli/config.py` as the storage backend (append to toml)
- Required files: `agentkit_cli/monitor_config.py`

- [ ] MonitorTarget dataclass with all fields
- [ ] MonitorConfig.load() reads from .agentkit.toml
- [ ] MonitorConfig.save() writes back without clobbering other sections
- [ ] add_target / remove_target / list_targets
- [ ] update_last_run() updates last_checked + last_score in config
- [ ] 12+ unit tests in tests/test_monitor_config.py

### D2. MonitorEngine + daemon runner (≥12 tests)

Build `agentkit_cli/monitor_engine.py`:
- `MonitorEngine`: orchestrates scheduled checks
- `check_target(target: MonitorTarget) -> MonitorResult` — runs agentkit analyze on the target, returns score + delta
- `MonitorResult` dataclass: target, score, prev_score, delta, timestamp, notify_fired (bool)
- `should_notify(result: MonitorResult) -> bool` — fires when abs(delta) >= alert_threshold
- `run_check(target: MonitorTarget)` — check + notify if needed + update config
- `run_all_due()` — check all targets whose `last_checked` is older than their schedule period
- Notification: reuse `NotificationEngine` from `agentkit_cli/notify.py` (exists from v0.21.0)
- Required files: `agentkit_cli/monitor_engine.py`

- [ ] MonitorResult dataclass
- [ ] check_target() uses ToolAdapter to run analyze (mocked in tests)
- [ ] should_notify() logic correct for threshold + min_score
- [ ] run_check() integrates check + notify + config update
- [ ] run_all_due() filters by schedule period
- [ ] 12+ unit tests in tests/test_monitor_engine.py (mock ToolAdapter)

### D3. `agentkit monitor` CLI command (≥15 tests)

Build `agentkit_cli/commands/monitor.py`:
- Typer app with subcommands: `add`, `remove`, `list`, `run`, `start`, `stop`, `status`, `logs`
- `add`: validate target, add to config, confirm
- `remove`: confirm removal
- `list`: Rich table showing target, schedule, last score, last checked, next due, notify configured (✓/✗)
- `run`: call MonitorEngine.run_all_due() or specific target; Rich output showing score + delta
- `start`: write daemon to background subprocess (daemonize via subprocess.Popen with stdout/stderr to log file); write PID file
- `stop`: read PID file, send SIGTERM
- `status`: show daemon running/stopped + next scheduled run times
- `logs`: tail from monitor.log or DB entries

Wire into `agentkit_cli/main.py` as `@app.command("monitor")` with subcommands.

- [ ] `agentkit monitor add github:owner/repo` works end-to-end
- [ ] `agentkit monitor list` shows Rich table
- [ ] `agentkit monitor run` runs checks and shows results
- [ ] `agentkit monitor start/stop/status` control daemon lifecycle
- [ ] `agentkit monitor logs` shows recent checks
- [ ] 15+ tests in tests/test_monitor_cmd.py

### D4. Daemon background process (≥8 tests)

Build `agentkit_cli/monitor_daemon.py`:
- Entry point for the background process (called by `monitor start` via subprocess)
- Simple polling loop: every 60 seconds, call `run_all_due()`, sleep remainder
- Writes structured JSON lines to `~/.agentkit/monitor.log` for `monitor logs` to parse
- Handles SIGTERM gracefully (flush log, exit)
- `~/.agentkit/` directory created if not exists

- [ ] Daemon starts, polls, handles SIGTERM
- [ ] Structured log output (JSON lines with ts, target, score, delta, notify_fired)
- [ ] `monitor logs` reads and formats the log
- [ ] 8+ tests in tests/test_monitor_daemon.py (process lifecycle tests, can be integration-style)

### D5. Docs, CHANGELOG, version bump, BUILD-REPORT (≥5 tests)

- Update README.md with `agentkit monitor` section (add/list/run/start/stop examples)
- Update CHANGELOG.md with v0.47.0 entry
- Bump version to 0.47.0 in `agentkit_cli/__init__.py` and `pyproject.toml`
- Write `BUILD-REPORT.md` with deliverable status + test count
- Update `agentkit doctor` to check for monitor daemon status
- [ ] README section added
- [ ] CHANGELOG entry added
- [ ] Version bumped to 0.47.0
- [ ] BUILD-REPORT.md complete
- [ ] 5+ tests verifying version string and docs content

## 4. Test Requirements

- [ ] Unit tests for each deliverable (D1: 12+, D2: 12+, D3: 15+, D4: 8+, D5: 5+) = 52+ new tests
- [ ] Baseline: 1969 tests. Target: ≥2021 tests
- [ ] All existing tests must still pass
- [ ] Tests must mock ToolAdapter/analyze calls (no real GitHub/network calls in unit tests)
- [ ] Daemon tests can use subprocess launch with short sleep + SIGTERM

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected → STOP, report
- All tests passing but deliverables remain → continue to next deliverable

## 7. Existing Code to Reference

Before writing code, read these existing files:
- `agentkit_cli/config.py` — ConfigManager, .agentkit.toml structure
- `agentkit_cli/notify.py` — NotificationEngine (from v0.21.0)
- `agentkit_cli/tool_adapter.py` — ToolAdapter (from v0.34.0)
- `agentkit_cli/commands/run_cmd.py` — pattern for orchestrating toolkit tools
- `agentkit_cli/commands/watch.py` — pattern for background/daemon-style commands
- `tests/test_monitor_config.py` — doesn't exist yet, you're creating it
- `agentkit_cli/history.py` — HistoryDB for storing run results
