# All-Day Build Contract: agentkit-cli v0.32.0 — `agentkit serve`

Status: In Progress
Date: 2026-03-16
Owner: Codex execution pass
Scope type: Deliverable-gated

## 1. Objective

Build a local web dashboard server for the agentkit toolkit. `agentkit serve` starts a lightweight HTTP server that shows a live dashboard of all toolkit runs from the history SQLite database, with auto-refresh. This makes local demos trivially easy: run `agentkit serve`, open browser, show live quality evolution. No expiring here.now URLs needed for demos.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (existing 1212 + new tests).
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.
11. Use only stdlib for the HTTP server (http.server or http.server + threading). No new dependencies.

## 3. Feature Deliverables

### D1. `agentkit_cli/serve.py` — core server module

Build a lightweight HTTP server using Python stdlib (`http.server`, `threading`) that:
- Reads from the existing history SQLite DB (`~/.agentkit/history.db`)
- Serves a dark-theme HTML dashboard on `localhost:PORT` (default 7890)
- Dashboard shows: latest run per project (project name, overall score, per-tool breakdown, timestamp, run ID)
- Auto-refreshes every 30s via `<meta http-equiv="refresh">` or JS `setInterval`
- Supports `--port PORT` flag
- Supports `--open` flag to auto-open browser (use `webbrowser.open()`)
- Server runs until Ctrl-C

Required files:
- `agentkit_cli/serve.py` — `AgenkitDashboard(BaseHTTPRequestHandler)` class, `start_server(port, open_browser)` function

- [ ] HTTP server using stdlib only
- [ ] Dashboard HTML generated from history DB query
- [ ] Auto-refresh (30s interval)
- [ ] `--port` and `--open` flags
- [ ] Graceful shutdown on Ctrl-C
- [ ] Tests for D1 (mock server, dashboard HTML generation)

### D2. CLI command — `agentkit serve`

Wire `serve` into the agentkit CLI (registered in `agentkit_cli/main.py` and `agentkit_cli/commands/`).

Required files:
- `agentkit_cli/commands/serve_cmd.py`
- Updated `agentkit_cli/main.py` to register `serve` subcommand

Flags:
- `--port PORT` (default 7890)
- `--open` (auto-open browser on start)
- `--json` (print server URL and status as JSON instead of starting server — useful for tests)
- `--once` (render dashboard once to stdout as HTML and exit — for testing/scripting)

- [ ] `serve_cmd.py` with all flags
- [ ] Registered in `main.py`
- [ ] `--once` flag outputs HTML to stdout and exits (no server started)
- [ ] Tests for D2 (CLI help, `--once` output, `--json` mode)

### D3. Dashboard HTML quality

The dashboard HTML must:
- Match the dark-theme aesthetic of existing agentkit HTML reports (dark background `#0f172a`, card style, Rich-style colors)
- Show a summary bar: total runs, unique projects, average score
- Show a table: Project | Latest Score | Grade | Tools Run | Timestamp | Run ID
- Score colored: green ≥80, yellow ≥60, red <60 (matching existing badge colors)
- Grade: A/B/C/D/F based on score (matching existing `agentkit score` logic)
- If history DB is empty: show "No runs yet. Try: agentkit run --help" message
- Include a "Refresh" button that triggers page reload
- Include the agentkit version in the footer

Required files:
- HTML template embedded in `agentkit_cli/serve.py` (no external template files)

- [ ] Dark-theme HTML matching existing reports
- [ ] Summary bar with totals
- [ ] Score-colored table rows
- [ ] Empty-state message
- [ ] Refresh button
- [ ] Version in footer
- [ ] Tests for D3 (HTML contains expected elements)

### D4. `--watch` variant behavior

When `agentkit run --serve` is used (optional integration), print the server URL after run completes. This is just a print statement addition, not a new subcommand.

Also add `agentkit serve` entry to `agentkit doctor` toolchain checks — verify serve command exists and is importable.

Required files:
- Minor additions to `agentkit_cli/commands/run_cmd.py` (add `--serve` flag, print URL if set)
- Minor addition to `agentkit_cli/commands/doctor_cmd.py` (serve check)

- [ ] `--serve` flag on `agentkit run` prints `Dashboard: http://localhost:7890` after run
- [ ] `agentkit doctor` reports serve availability
- [ ] Tests for D4

### D5. Docs + version bump to v0.32.0

- [ ] `__init__.py` → `0.32.0`
- [ ] `pyproject.toml` → `0.32.0`
- [ ] `CHANGELOG.md` — add v0.32.0 entry with feature description
- [ ] `README.md` — add "Local Dashboard" section after Notifications section
- [ ] `BUILD-REPORT.md` — complete with all deliverable statuses and final test count
- [ ] `progress-log.md` — append final entry

## 4. Test Requirements

Target: 40+ new tests (existing baseline: 1212)

- [ ] `tests/test_serve.py`: server starts/stops, dashboard HTML generation, `--once` mode, `--json` mode, empty-state, score coloring, grade logic
- [ ] `tests/test_serve_cmd.py` or integrated into test_serve: CLI flags, help text
- [ ] All 1212 existing tests still pass
- [ ] Tests must NOT actually start a real server on a real port (use `--once` or mock the server)

## 5. Reports

- Write to `progress-log.md` after each deliverable:
  - What was built
  - Tests passing count
  - Any blockers
- `BUILD-REPORT.md`: complete summary when done

## 6. Stop Conditions

- All deliverables checked + `python3 -m pytest -q` passes with 0 failures → DONE
- 3 consecutive failed attempts on same issue → STOP, write blocker report to `progress-log.md`
- Scope creep (new requirements discovered mid-build) → STOP, document in progress-log
- All tests passing but deliverables remain → continue to next deliverable

## 7. What NOT To Do

- Do NOT add external dependencies (no Flask, no FastAPI, no Jinja2). stdlib only.
- Do NOT change the history DB schema — read it as-is.
- Do NOT modify existing test files except to add new tests.
- Do NOT deploy anywhere (no here.now publish, no git push — build-loop handles that).
- Do NOT modify files outside ~/repos/agentkit-cli/.
