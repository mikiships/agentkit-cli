# All-Day Build Contract: `agentkit api` — Local REST API Server

Status: In Progress
Date: 2026-03-22
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentkit api` — a lightweight FastAPI REST server that exposes the core agentkit-cli analysis pipeline as HTTP endpoints. The server enables:
- **Durable shareable URLs** (badge embeds, permalinks, third-party integrations) that don't expire like here.now
- **Zero-install demos** via a public ngrok tunnel URL
- **shields.io-compatible badge endpoint** so repos can embed live agent-readiness scores in their README

This is the bridge between CLI-only tool and embeddable web component.

The server uses the existing SQLite history DB as its data store — results from CLI runs are immediately available via API.

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
11. Do NOT run long-running servers or start actual HTTP servers during tests — use TestClient from httpx/starlette.testclient only.
12. Do NOT publish to PyPI. The build-loop handles PyPI publishing.

## 3. Context

- Repo: ~/repos/agentkit-cli
- Current version: 0.89.0
- Target version: 0.90.0
- History DB: `~/.local/share/agentkit/history.db` (SQLite)
- Existing analysis pipeline: `agentkit analyze github:owner/repo` → stores result in history DB
- Add `fastapi` and `httpx` (for TestClient) to optional dependencies in pyproject.toml only — do NOT add as hard dependencies

## 4. Feature Deliverables

### D1. Core API Server (`agentkit_cli/api_server.py`)

FastAPI application with these endpoints:

1. **`GET /`** — health check + version info JSON
2. **`GET /analyze/{owner}/{repo}`** — analyze a GitHub repo (reads from DB cache first, triggers fresh analysis if >24h stale or not found). Returns: `{repo, score, grade, last_analyzed, details}`.
3. **`GET /score/{owner}/{repo}`** — same as analyze but lightweight (DB-only, no fresh analysis). Returns 404 if not in DB.
4. **`GET /badge/{owner}/{repo}`** — shields.io-compatible JSON endpoint. Returns `{schemaVersion: 1, label: "agent score", message: "95/A", color: "brightgreen"}`. Color mapping: 90+="brightgreen", 70+="yellow", 50+="orange", else="red".
5. **`GET /trending`** — top 10 repos from history DB ordered by score. Query params: `?limit=10&min_score=0`.
6. **`GET /history/{owner}/{repo}`** — score history for a repo from DB. Returns list of `{timestamp, score, grade}`.
7. **`GET /leaderboard`** — top repos by score, with grade badges. Query params: `?limit=20`.

Error handling: 404 for unknown repos, 422 for bad params, 500 with message for analysis failures.

Required files:
- `agentkit_cli/api_server.py` — FastAPI app, all endpoints, CORS enabled (allow all origins for demo use)

- [ ] FastAPI app with 7 endpoints
- [ ] Reads from history DB via existing HistoryDB class
- [ ] `analyze` endpoint triggers `agentkit analyze` subprocess if cache stale/missing
- [ ] shields.io badge endpoint with color coding
- [ ] CORS middleware enabled
- [ ] Tests for D1 (≥15 tests using TestClient — mock subprocess calls, use real SQLite in-memory)

### D2. CLI command (`agentkit api`)

Wires the FastAPI server into the CLI.

```
agentkit api [--host 127.0.0.1] [--port 8742] [--reload] [--share]
```

- `--host` default: `127.0.0.1`
- `--port` default: `8742`
- `--reload` for dev mode (uvicorn auto-reload)
- `--share` starts ngrok tunnel (if `ngrok` binary exists in PATH) and prints the public URL

Startup message: prints base URL + badge URL example + trending URL.

Required files:
- `agentkit_cli/commands/api_cmd.py` — CLI command using typer
- `agentkit_cli/main.py` — register `api` command

Add to optional dependencies in `pyproject.toml`:
```toml
[project.optional-dependencies]
api = ["fastapi>=0.100.0", "uvicorn>=0.23.0", "httpx>=0.24.0"]
```

- [ ] `agentkit api` CLI command with --host/--port/--reload/--share flags
- [ ] Startup message with usage examples
- [ ] Graceful `ImportError` message if fastapi not installed ("Run: pip install agentkit-cli[api]")
- [ ] Tests for D2 (≥10 tests)

### D3. `agentkit doctor` integration + `--api` flag on `agentkit run`

1. Add `api.reachable` check to `agentkit doctor`: tries `GET http://127.0.0.1:8742/` with 1s timeout. Reports PASS if responding, WARN if not (non-fatal). Category: `api`.

2. `agentkit run --api-cache`: after run, POST result to local API if it's running (best-effort, non-blocking, 2s timeout). This keeps the API cache warm automatically.

Required files:
- Update `agentkit_cli/doctor.py` — add api check
- Update `agentkit_cli/runner.py` (or equivalent) — add --api-cache flag

- [ ] `agentkit doctor` api category with reachability check
- [ ] `agentkit run --api-cache` flag
- [ ] Tests for D3 (≥8 tests)

### D4. Dark-theme HTML status page at `GET /ui`

When you open `http://localhost:8742/ui` in a browser, you see a minimal dark-theme status page showing:
- Server version + uptime
- Total repos in DB
- Recent analyses (last 5 runs)
- Badge embed snippet: `![Agent Score](http://localhost:8742/badge/owner/repo)` 
- Direct link to `/trending` as JSON

This is a "live demo page" for when you share the ngrok URL.

Required files:
- Add `GET /ui` route to `agentkit_cli/api_server.py` returning HTML (inline HTML string, no template engine dependency)

- [ ] `/ui` endpoint returning dark-theme HTML
- [ ] Shows server stats + recent runs from DB
- [ ] Badge embed code snippet
- [ ] Tests for D4 (≥8 tests)

### D5. Docs, version bump, BUILD-REPORT, CHANGELOG

- `docs/api.md`: full API docs with example curl commands for all 7 endpoints + badge embed snippet
- `pyproject.toml`: version bumped to `0.90.0`
- `agentkit_cli/__init__.py`: version bumped to `0.90.0`
- `CHANGELOG.md`: `[0.90.0]` entry
- `BUILD-REPORT.md`: updated with v0.90.0 header + summary + test count
- `BUILD-REPORT-v0.90.0.md`: versioned copy

- [ ] docs/api.md written
- [ ] pyproject.toml version = "0.90.0"
- [ ] __init__.py version = "0.90.0"
- [ ] CHANGELOG.md has [0.90.0] entry
- [ ] BUILD-REPORT.md header updated to v0.90.0
- [ ] BUILD-REPORT-v0.90.0.md created
- [ ] All tests passing

## 5. Test Requirements

- [ ] All 7 API endpoints tested with TestClient (mocked subprocess for analyze)
- [ ] Badge color coding tested (brightgreen/yellow/orange/red thresholds)
- [ ] CLI command tested (import check, --host/--port flags)
- [ ] Doctor api check tested (mock HTTP)
- [ ] Error cases: 404 unknown repo, graceful ImportError
- [ ] All existing tests still pass
- Target: ≥4418 (baseline) + ≥41 new = ≥4459 total

## 6. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 7. Stop Conditions

- All deliverables checked and all tests passing → DONE
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected → STOP, report what's new
- Any test in the existing suite breaks → fix before proceeding, do not skip
