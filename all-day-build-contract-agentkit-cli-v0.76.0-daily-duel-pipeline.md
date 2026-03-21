# All-Day Build Contract: agentkit-cli v0.76.0 — daily-duel tweet quality + posting pipeline

Status: In Progress  
Date: 2026-03-21  
Owner: Codex execution pass  
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

The `agentkit daily-duel` command (v0.75.0) auto-selects GitHub repo pairs and outputs tweet-ready text.
Problem: when both repos score 100/100 (extremely common for popular OSS), the tweet is boring:
> "expressjs/express vs fastify/fastify agent-readiness: … Winner: draw on 0/4 dimensions."

This contract improves tweet quality for draws and ties, wires the daily-duel into the x-organic posting pipeline, and ships v0.76.0.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (currently 3781 passing).
4. New features must ship with docs and CHANGELOG entry.
5. Never modify files outside the project directory (~repos/agentkit-cli).
6. Commit after each completed deliverable.
7. If stuck on same issue for 3 attempts, stop and write a blocker report.
8. Do NOT refactor, restyle, or "improve" code outside the deliverables.
9. Read existing tests before writing new code.
10. Version bump: 0.75.0 → 0.76.0

## 3. Feature Deliverables

### D1. Improved tweet_text generation for draws and near-draws

Current behavior: "Winner: draw on 0/4 dimensions." — zero personality, zero insight.

Required changes in `agentkit_cli/commands/daily_duel_cmd.py` and any shared duel tweet logic:

1. **Draw case (both scores equal):** Switch to an angle focused on BOTH repos being high-quality. Examples:
   - "expressjs/express vs fastify/fastify: both score 100/100 — a draw of champions. In the web-frameworks category, the best repos write for humans and agents."
   - "astral-sh/uv vs pypa/pip: both score 100/100. Top devtools repos maintain exceptional agent-readiness — no surprises."
   The pattern: `{repo1} vs {repo2}: {scores} draw. {category insight}` — humanize with category context.

2. **Near-draw case (score diff ≤ 5):** Lead with the margin being close. Example:
   - "django/django (98/100) vs tiangolo/fastapi (95/100): extremely close. Django edges FastAPI by 3 points across 4 agent-readiness dimensions."

3. **Clear winner case (diff > 5):** Current format is acceptable. Keep it.

4. Add a dict of `CATEGORY_INSIGHTS` keyed by pair_category with ~3-5 short phrases per category. Used to vary the draw-case copy:
   ```python
   CATEGORY_INSIGHTS = {
       "web-frameworks": ["top web frameworks maintain excellent agent docs", ...],
       "devtools": ["leading devtools set the bar for agent-readiness", ...],
       # etc.
   }
   ```
   Pick insight based on `hash(seed) % len(phrases)` for determinism.

5. Keep tweet_text ≤ 280 chars. Truncate at 277 + "..." if over.

Tests required: ≥ 8 new tests in `tests/test_daily_duel.py` covering draw, near-draw, clear-winner, and category-insight variation.

### D2. `agentkit daily-duel --tweet-only` flag

Add a `--tweet-only` flag that prints ONLY the tweet text (no Rich table, no headers, no Panel) and exits.
This enables piping: `agentkit daily-duel --tweet-only | frigatebird tweet`

Requirements:
- `--tweet-only` flag on the daily-duel CLI
- If `--tweet-only` is set: print tweet_text to stdout, nothing else
- Works with `--pair`, `--seed`, default auto-select modes
- Tests: ≥ 4 tests

### D3. Write daily-duel-latest.json properly on every run

Ensure `~/.local/share/agentkit/daily-duel-latest.json` is always written after every successful run, including the tweet_text field.
The x-organic-posts cron already checks certain workspace files; this file will be its source for daily-duel content.

Requirements:
- Verify `_write_latest_json` is called on all code paths (auto-pair and explicit pair)
- File must contain at minimum: `repo1`, `repo2`, `pair_category`, `tweet_text`, `run_date`, `winner`, `repo1_score`, `repo2_score`
- Tests: ≥ 3 tests verifying file is written with correct fields

### D4. Posting helper script: `scripts/post-daily-duel.sh`

New script that:
1. Runs `agentkit daily-duel --tweet-only` to get tweet text
2. Checks the tweet is non-empty and ≤ 280 chars
3. Posts via `frigatebird tweet "<text>"`
4. Exits 0 on success, 1 on failure
5. Logs the result to `~/.local/share/agentkit/daily-duel-post-log.jsonl` with: `{ts, date, tweet_text, status, frigatebird_output}`

Location: `~/repos/agentkit-cli/scripts/post-daily-duel.sh`

This script is what the cron will call; it handles the frigatebird dependency gracefully (if frigatebird not found, exit 1 with clear message).

Tests: This is a shell script, no pytest needed. But add a smoke note in BUILD-REPORT.md.

### D5. CHANGELOG, version bump, BUILD-REPORT

- Bump `__version__` in `agentkit_cli/__init__.py` from `0.75.0` to `0.76.0`
- Update `pyproject.toml` version to `0.76.0`
- Add CHANGELOG entry for `[0.76.0]`
- Update BUILD-REPORT.md with deliverables, test count, and any build notes

## 4. Validation Gates

Before marking complete, verify:

- [ ] All 5 deliverables implemented and committed
- [ ] `pytest -q` passes with ≥ 3781 original tests + ≥ 15 new tests
- [ ] `agentkit daily-duel --tweet-only` prints only tweet text
- [ ] Draw case produces a human-readable tweet (no "draw on 0/4 dimensions")
- [ ] `~/.local/share/agentkit/daily-duel-latest.json` written with all required fields
- [ ] `scripts/post-daily-duel.sh` exists and is executable
- [ ] `__version__` == "0.76.0"
- [ ] CHANGELOG entry written
- [ ] All changes committed to git (not just working tree)

## 5. Stop Conditions

- Stop if the same failing test appears after 3 fix attempts — write blocker to BUILD-REPORT.md
- Do NOT add new commands beyond D1-D5
- Do NOT upgrade dependencies
- Do NOT modify files outside ~/repos/agentkit-cli/

## 6. Output

- Write BUILD-REPORT.md to ~/repos/agentkit-cli/BUILD-REPORT.md
- Write progress notes to ~/repos/agentkit-cli/progress-log.md
- Do NOT push to PyPI (build-loop handles publishing)
- Do NOT push to GitHub (build-loop handles tagging)
