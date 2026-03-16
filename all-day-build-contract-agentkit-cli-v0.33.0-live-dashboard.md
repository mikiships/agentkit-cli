# All-Day Build Contract: agentkit-cli v0.33.0 — Live Watch+Serve Integration

Status: In Progress
Date: 2026-03-16
Owner: Mordecai build-loop
Codex surface: CLI
Model: claude-sonnet-4-6 (subagent)
Scope type: Deliverable-gated (no hour promises)
Repo: mikiships/agentkit-cli
Working directory: ~/repos/agentkit-cli
Branch: main

---

## 0. Agent Instructions

You are building `agentkit-cli v0.33.0`. Follow this contract exactly.
Do NOT ask "should I continue?" — always proceed to the next unchecked deliverable.
Declare completion ONLY when all deliverables are checked and the validation gate passes.
Commit after each completed deliverable.
Do NOT refactor, restyle, or improve code outside the explicit deliverables.
Do NOT publish to PyPI. Do NOT run `twine upload` or `pip publish`. Build-loop handles publishing.

---

## 1. Objective

Add SSE (Server-Sent Events) live-push to the existing `agentkit serve` dashboard, and wire `agentkit watch --serve` so a single command runs the file-watcher + HTTP server together, with the dashboard updating in real-time without a page reload.

Existing code to extend (do NOT rewrite unless necessary):
- `agentkit_cli/serve.py` — the HTTP server (stdlib BaseHTTPRequestHandler)
- `agentkit_cli/commands/serve_cmd.py` — the serve CLI command
- `agentkit_cli/commands/watch.py` — the file-watcher
- `agentkit_cli/main.py` — CLI entry point

---

## 2. Non-Goals

- Do NOT use Flask, FastAPI, aiohttp, or any external HTTP library. Stdlib only.
- Do NOT rewrite the existing dashboard HTML from scratch — extend it.
- Do NOT modify any command outside this contract's scope (analyze, gate, score, etc.).
- Do NOT publish to PyPI.
- Do NOT add authentication or multi-user features.

---

## 3. Deliverables

### D1: SSE endpoint in `agentkit_cli/serve.py`

Add a thread-safe SSE broker class and `/events` route to the existing `AgentKitHandler`.

Requirements:
- `SseBroker` class: thread-safe client registration with `Queue`, `broadcast(data: str)` method that sends to all connected clients, auto-remove disconnected clients
- `AgentKitHandler` handles GET `/events` → returns `Content-Type: text/event-stream`, keeps connection open, receives from broker queue
- `AgentKitHandler` handles GET `/api/runs` → returns JSON array of latest runs (extract from existing `_query_latest_runs`)
- The existing GET `/` dashboard route must still work unchanged
- The broker instance is module-level (singleton per server process)
- `start_server()` function signature must remain compatible: `start_server(port, open_browser, db_path)` — add optional `live: bool = False` kwarg
- When `live=True`, `start_server` starts a background thread that polls the DB every 5s and calls `broker.broadcast(json.dumps({"type": "refresh"}))` if run count changed

Commit message: `D1: SSE broker + /events + /api/runs in serve.py`

### D2: Dashboard JS for live updates

Update the `_render_dashboard_html()` function in `serve.py` to include JavaScript that:
- Connects to `/events` via `new EventSource('/events')`
- On message: fetches `/api/runs`, re-renders the runs table in-place (no full page reload)
- Shows a "● Live" green indicator in the header when SSE is connected
- Shows "○ Offline" in grey when SSE is disconnected (e.g., server stopped)
- Reconnects automatically on connection drop (EventSource does this natively)

Keep the existing dark-theme styling. The table re-render must match the existing HTML structure exactly (same classes, same columns).

Commit message: `D2: dashboard JS EventSource for live table updates`

### D3: `agentkit watch --serve [--port N]` combined mode

Extend `agentkit_cli/commands/watch.py` to support a `--serve` flag.

When `--serve` is set:
- Start `agentkit serve` (the HTTP server) in a background thread before the watcher loop starts
- After each pipeline run completes (inside `_run_pipeline` or its post-hook), call `broker.broadcast(json.dumps({"type": "refresh"}))` to notify dashboard clients
- The watcher and server share the same process (no subprocess for serve)
- Print startup message: `Watching <path>  •  Dashboard: http://localhost:<port>`
- `--port` kwarg defaults to `DEFAULT_PORT` (7890) from serve.py

Import `start_server` and `SseBroker` from `agentkit_cli.serve`. The serve thread should be daemon=True so it dies when the watcher exits.

Commit message: `D3: agentkit watch --serve combined mode`

### D4: `agentkit serve --live` polling mode

Extend `agentkit_cli/commands/serve_cmd.py` and `serve_cmd` function:
- Add `--live` / `live: bool = False` flag
- When `--live` is passed, call `start_server(port=port, open_browser=open_browser, db_path=db_path, live=True)`
- This activates the background DB-polling thread (D1's `live=True` path), pushing SSE refresh events when new runs appear
- Print startup message: `Dashboard (live): http://localhost:<port>`

Commit message: `D4: agentkit serve --live flag for external-write polling`

### D5: Tests, docs, version bump

1. Write tests in `tests/test_serve_sse.py`:
   - `test_sse_broker_broadcast`: create SseBroker, connect 2 fake clients, broadcast, assert both receive
   - `test_api_runs_endpoint`: mock DB, hit `/api/runs`, assert JSON response
   - `test_watch_serve_flag_exists`: `agentkit watch --help` output contains `--serve`
   - `test_serve_live_flag_exists`: `agentkit serve --help` output contains `--live`
   - At least 8 tests total in this file

2. Update `README.md`: add "Live Dashboard" section after the existing `agentkit serve` section
   ```
   ## Live Dashboard

   Run once and watch scores update in real-time:

   ```bash
   # Combined: watch files + serve dashboard (updates without reload)
   agentkit watch --serve --port 7890

   # Or start server in live mode (polls for external writes):
   agentkit serve --live
   ```
   ```

3. Update `CHANGELOG.md` with v0.33.0 entry (date 2026-03-16)
4. Bump version to `0.33.0` in `agentkit_cli/__init__.py` and `pyproject.toml`
5. Update `BUILD-REPORT.md` with a brief summary of what was built

Commit message: `D5: tests, README, CHANGELOG, v0.33.0 bump`

---

## 4. Validation Gate

The contract is complete ONLY when:

```bash
cd ~/repos/agentkit-cli
python3 -m pytest -q --tb=short 2>&1 | tail -5
```

Shows: `N passed` with zero failures (N >= 1276, i.e., 1268 baseline + 8 new).

AND:
```bash
agentkit watch --help | grep -q "serve" && echo "PASS"
agentkit serve --help | grep -q "live" && echo "PASS"
python3 -c "from agentkit_cli.serve import SseBroker; print('PASS')"
```

All three print "PASS".

AND version in `agentkit_cli/__init__.py` is `0.33.0`.

---

## 5. Stop Conditions

Stop and write a blocker report if:
- The test suite drops below the 1268 baseline at any point after D1
- You cannot import `SseBroker` from `agentkit_cli.serve` after D1
- You are stuck on the same issue for 3+ attempts

---

## 6. Output

When complete, write a brief summary to `BUILD-REPORT.md` at the repo root (append, don't overwrite).
Format:
```
## v0.33.0 — Live Dashboard (YYYY-MM-DD)
- D1: SSE broker + /events + /api/runs
- D2: Dashboard JS live updates
- D3: agentkit watch --serve
- D4: agentkit serve --live
- D5: Tests (N passing), docs, version bump
```
