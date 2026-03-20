# All-Day Build Contract: agentkit-cli v0.75.0 — `agentkit daily-duel`

Status: In Progress  
Date: 2026-03-20  
Owner: Codex execution pass  
Scope type: Deliverable-gated

## 1. Objective

Add `agentkit daily-duel` — a zero-input command that automatically selects two well-known, contrasting GitHub repos, runs a repo-duel between them, generates a shareable dark-theme HTML report, and outputs tweet-ready text.

**Why:** The x-organic-posts cron needs a steady supply of concrete data to tweet without requiring Josh to manually curate. `agentkit daily-duel` produces fact-based comparison content autonomously. Each run picks a fresh pair (e.g. fastapi vs flask, react vs vue, httpx vs requests), duels them, and outputs a 280-char tweet stub + share URL. The organic posts cron reads from the output file and decides whether to post.

**Target:** This is the distribution flywheel. Strong data → shareable tweet → organic reach → tool discovery.

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

## 3. Feature Deliverables

### D1: DailyDuelEngine — preset repo pairs and deterministic picker (≥12 tests)
File: `agentkit_cli/commands/daily_duel.py`

**Preset pairs** — must include at least 20 interesting contrasting pairs across categories:
- Web frameworks: fastapi/fastapi vs pallets/flask, django/django vs fastapi/fastapi, tiangolo/fastapi vs encode/starlette
- HTTP clients: encode/httpx vs psf/requests, urllib3/urllib3 vs encode/httpx
- ML/AI: huggingface/transformers vs openai/openai-python, langchain-ai/langchain vs microsoft/semantic-kernel
- Testing: pytest-dev/pytest vs robotframework/robotframework
- Async: python-trio/trio vs encode/uvicorn
- DB: sqlalchemy/sqlalchemy vs mongodb/mongo-python-driver
- JS/TS: vercel/next.js vs remix-run/remix, facebook/react vs vuejs/vue
- Devtools: astral-sh/uv vs pypa/pip, astral-sh/ruff vs PyCQA/flake8

`DailyDuelEngine`:
- `pick_pair(seed: str = None) -> Tuple[str, str]` — deterministic daily pick from presets. Default seed = today's date YYYY-MM-DD so the same pair runs all day. With custom seed = any string for ad-hoc picks.
- `run_daily_duel(seed: str = None, deep: bool = False) -> DailyDuelResult`
  - Calls RepoDuelEngine.run_duel() on picked pair
  - Adds `tweet_text: str` to DailyDuelResult — 280-char tweet template: "{repo1} vs {repo2} agent-readiness: {repo1} {score1}/100 ({grade1}), {repo2} {score2}/100 ({grade2}). Winner: {winner} on {N}/{total} dimensions. [shareUrl]"
  - Adds `pair_category: str` (e.g. "web-frameworks")
  - Adds `seed: str`
- `DailyDuelResult` extends `RepoDuelResult` with: `tweet_text`, `pair_category`, `seed`

Output JSON file: `~/.local/share/agentkit/daily-duel-latest.json` — written on every run. This is how x-organic-posts cron reads the latest result.

- [ ] 20+ preset pairs defined
- [ ] pick_pair() deterministic by date seed
- [ ] run_daily_duel() delegates to RepoDuelEngine
- [ ] tweet_text generated and ≤280 chars
- [ ] JSON output to ~/.local/share/agentkit/daily-duel-latest.json
- [ ] Tests for D1 (≥12)

### D2: `agentkit daily-duel` CLI command (≥10 tests)
Wire into main CLI.

```
agentkit daily-duel [--seed TEXT] [--deep] [--share] [--json] [--output FILE] [--pair REPO1 REPO2] [--quiet]
```

- `--pair REPO1 REPO2`: override the auto-pick with explicit repos (reuses RepoDuelEngine directly)
- `--seed TEXT`: custom seed instead of today's date  
- `--share`: upload HTML report to here.now, include URL in tweet_text
- `--json`: print DailyDuelResult as JSON to stdout
- `--output FILE`: write HTML report to file
- `--quiet`: suppress rich output, only print tweet_text

Rich terminal output:
- Header: "Daily Duel: {repo1} vs {repo2}"
- Category badge
- Full repo-duel Rich output (reuse RepoDuelHTMLRenderer CLI output)
- Box at the bottom: "Tweet-ready: {tweet_text}"

Saves to history DB with label `daily_duel`.

- [ ] CLI wired into main
- [ ] --pair override works
- [ ] --seed works for reproducibility
- [ ] --share uploads and tweet_text includes URL
- [ ] --json outputs DailyDuelResult
- [ ] daily-duel-latest.json written on every successful run
- [ ] Tests for D2 (≥10)

### D3: `agentkit daily-duel --calendar` — 7-day schedule preview (≥8 tests)
- `agentkit daily-duel --calendar` prints the upcoming 7 daily pairs (Mon–Sun) as a Rich table
- No analysis run, just shows which pairs are scheduled
- Good for social media content planning

- [ ] --calendar flag implemented
- [ ] Shows 7 days of pairs (date + repo1 + repo2 + category)
- [ ] Tests for D3 (≥8)

### D4: Docs, version bump, BUILD-REPORT (≥5 tests)
- README: add `agentkit daily-duel` section with example and tweet output
- CHANGELOG: entry for v0.75.0
- Version: bump `agentkit_cli/__init__.py` to `0.75.0`
- `pyproject.toml`: version bump to `0.75.0`
- BUILD-REPORT.md: final summary

- [ ] README updated
- [ ] CHANGELOG updated  
- [ ] Version set to 0.75.0 in both __init__.py and pyproject.toml
- [ ] BUILD-REPORT.md written

## 4. Test Requirements

- Baseline: 3743 tests (v0.74.0)
- Target: 3743 + 35 new tests = 3778+ total
- No regressions allowed
- Tests must use mocked analyze/duel calls — do not make real GitHub API calls in tests
- daily-duel-latest.json write path must be tested with a temp dir fixture

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Final summary when all deliverables done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected → STOP, report
- All tests passing but deliverables remain → continue to next deliverable

## 7. Notes for Builder

- RepoDuelEngine is in `agentkit_cli/commands/repo_duel.py` (shipped in v0.74.0)
- RepoDuelHTMLRenderer is in `agentkit_cli/renderers/repo_duel_renderer.py`
- The `analyze` command + ToolAdapter is the correct way to run per-repo analysis
- here.now upload pattern: see `agentkit_cli/commands/share.py`
- History DB pattern: see `agentkit_cli/history.py`
- JSON output file: write atomically (write to tmp, rename)
- tweet_text must be ≤280 chars including the share URL. If no --share, omit URL from count.
