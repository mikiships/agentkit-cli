# agentkit API — REST Server Documentation

The `agentkit api` command starts a lightweight FastAPI REST server that exposes the agentkit analysis pipeline as HTTP endpoints.

## Quick Start

```bash
pip install agentkit-cli[api]
agentkit api
```

Server starts at `http://127.0.0.1:8742` by default.

## Options

```
agentkit api [--host HOST] [--port PORT] [--reload] [--share] [--interactive]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `127.0.0.1` | Bind host |
| `--port` | `8742` | Bind port |
| `--reload` | `false` | Enable uvicorn auto-reload (dev mode) |
| `--share` | `false` | Start ngrok tunnel and print public URL |
| `--interactive` | `false` | Confirm the /ui form is enabled (always on) |

## Endpoints

### `GET /` — Health Check

```bash
curl http://localhost:8742/
```

Response:
```json
{"status": "ok", "version": "0.90.0", "uptime_seconds": 42.1}
```

### `GET /analyze/{owner}/{repo}` — Analyze a Repo

Reads from DB cache first. Triggers fresh `agentkit analyze` if cache is >24h stale or missing.

```bash
curl http://localhost:8742/analyze/openai/openai-python
```

Response:
```json
{
  "repo": "openai/openai-python",
  "score": 87.5,
  "grade": "B",
  "last_analyzed": "2026-03-22T18:00:00+00:00",
  "details": null
}
```

### `GET /score/{owner}/{repo}` — Lightweight Score Lookup

DB-only, no fresh analysis. Returns 404 if not in DB.

```bash
curl http://localhost:8742/score/openai/openai-python
```

### `GET /badge/{owner}/{repo}` — shields.io Badge

```bash
curl http://localhost:8742/badge/openai/openai-python
```

Response:
```json
{
  "schemaVersion": 1,
  "label": "agent score",
  "message": "87/B",
  "color": "brightgreen"
}
```

**Color mapping:**
- `brightgreen` — score ≥ 90
- `yellow` — score ≥ 70
- `orange` — score ≥ 50
- `red` — score < 50

**Embed in README:**
```markdown
![Agent Score](https://your-ngrok-url/badge/owner/repo)
```

### `GET /trending` — Top Repos

```bash
curl "http://localhost:8742/trending?limit=10&min_score=70"
```

Query params: `limit` (1-100, default 10), `min_score` (0-100, default 0).

### `GET /history/{owner}/{repo}` — Score History

```bash
curl http://localhost:8742/history/openai/openai-python
```

Response:
```json
{
  "repo": "openai/openai-python",
  "history": [
    {"timestamp": "2026-03-22T18:00:00+00:00", "score": 87.5, "grade": "B"}
  ]
}
```

### `GET /leaderboard` — Full Leaderboard

```bash
curl "http://localhost:8742/leaderboard?limit=20"
```

### `POST /analyze` — Analyze a Repo (Interactive)

Submit a repo for analysis. Supports concurrent limiting (max 5) and caching (results < 1h old returned from cache).

```bash
curl -X POST http://localhost:8742/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo": "github:psf/requests"}'
```

Response:
```json
{
  "repo": "psf/requests",
  "score": 72.5,
  "grade": "C",
  "tool_results": {},
  "share_url": null,
  "elapsed_seconds": 45.2,
  "cached": false
}
```

Also available as GET: `GET /analyze?repo=github:psf/requests`

### `GET /recent` — Recent Analyses

```bash
curl "http://localhost:8742/recent?limit=10"
```

Response:
```json
{
  "analyses": [
    {"repo": "psf/requests", "score": 72.5, "grade": "C", "last_analyzed": "2026-03-22T20:00:00+00:00"}
  ],
  "total": 1
}
```

### `GET /ui` — Interactive Status Page

Open `http://localhost:8742/ui` in a browser to see:
- Interactive GitHub repo analysis form
- Loading spinner during analysis
- Results panel with score, grade, and tool breakdown
- Recent analyses panel (auto-refreshes every 30s)
- Badge embed snippet
- Links to trending/leaderboard/recent JSON

## Doctor Check

```bash
agentkit doctor
```

The `api.reachable` check verifies the API server is running at `http://127.0.0.1:8742`. Reports WARN (non-fatal) if not running.

## API Cache Warm-up

```bash
agentkit run --api-cache
```

After a pipeline run, `--api-cache` pings the local API server to keep the cache warm (best-effort, non-blocking).

## Public Sharing with ngrok

```bash
agentkit api --share
```

Requires `ngrok` in PATH. Prints the public HTTPS URL so you can share badge URLs publicly.
