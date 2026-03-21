# Build Contract: agentkit-cli v0.81.0 — `agentkit hot`

**Date:** 2026-03-21
**Owner:** builder sub-agent
**Baseline:** v0.80.0 — 3967 tests passing

## Objective

Add `agentkit hot` command: fetch GitHub's trending repos (today's list), score each with ExistingStateScorer, pick the most surprising finding, and output a tweet-ready insight. Also produce `post-hot.sh` script for frigatebird posting pipeline.

This is the third organic content pipeline alongside `daily-duel` and `spotlight`.

## Deliverables

### D1: `agentkit hot` command (≥20 tests)

- Fetch GitHub trending page (https://github.com/trending) via HTTP
- Parse repo names from trending list (today, default Python+JavaScript, configurable via --language)
- Score each via ExistingStateScorer (same as daily-duel uses)
- Find most interesting finding: either (a) top-trending repo with surprisingly low score, or (b) highly scored repo with rising stars
- `--tweet-only`: output just the tweet text, no Rich table
- `--language <lang>`: filter trending by language (default: no filter = all)
- `--limit N`: how many trending repos to score (default: 10, max: 25)
- `--share`: upload HTML report to here.now, include URL in tweet
- `--json`: structured output
- Tweet format: concise, observation-led, <280 chars. Example: "flask is trending on GitHub today and already agent-ready (91/100). httpx next to it scores 87. The Python ecosystem is cleaning up its docs." OR "tornado is #3 trending today but scores 31/100 — missing CONTRIBUTING, CHANGELOG, type annotations. High traffic, low agent context."
- Must use ExistingStateScorer (do NOT run agentmd first — same circular scoring fix as daily-duel)

### D2: HTML report (≥10 tests)

- Dark-theme HTML table with all scored trending repos
- Ranked by ExistingState score
- Highlight the "most surprising" finding at top
- `--share` flag to upload to here.now

### D3: `post-hot.sh` script (≥5 tests = script presence + dry-run output validation)

- Location: `scripts/post-hot.sh`
- Same pattern as `post-daily-duel.sh` and `post-spotlight.sh`
- Usage: `./post-hot.sh` or `./post-hot.sh --share` or `./post-hot.sh --dry-run`
- Calls `agentkit hot --tweet-only` (or `--tweet-only --share` with `--share`)
- Posts via `frigatebird tweet "<text>"`
- Logs to `~/.local/share/agentkit/hot-post-log.jsonl`
- `--dry-run`: print tweet text, skip frigatebird
- Exit 0 on success, non-zero on error

### D4: Integration into doctor + run (≥5 tests)

- `agentkit doctor` should detect the `hot` command is available
- `agentkit run --all` should include hot in the pipeline (optional, can be --no-hot to skip)
- OR: just add a `hot` check to doctor that verifies GitHub trending is reachable

### D5: Docs, CHANGELOG, version bump, BUILD-REPORT (≥5 tests)

- README: new section "Trending Repos" under Content Pipeline commands
- CHANGELOG: v0.81.0 entry
- `__version__` = "0.81.0" in `agentkit_cli/__init__.py`
- BUILD-REPORT.md in repo root: date, what shipped, test count, deliverable status
- pyproject.toml version = "0.81.0"

## Target test count

3967 baseline + ≥45 new = ≥4012 total

## Stop conditions

- STOP if GitHub trending fetch fails and cannot be worked around — report what was attempted
- STOP if ExistingStateScorer is not importable — check the actual module path before writing code
- DO NOT run agentmd generate before scoring (would cause circular 100/100 issue)
- DO NOT publish to PyPI — build-loop handles publish
- DO NOT push to GitHub — build-loop handles push

## Technical notes

- ExistingStateScorer is in `agentkit_cli/existing_scorer.py` (check the actual path first)
- trending fetch: simple `requests.get("https://github.com/trending?since=daily&l=<lang>")`, parse `<h2 class="h3 lh-condensed">` links
- Fallback if trending fetch fails: use 10 hardcoded well-known repos and note "trending fetch unavailable"
- Keep HTTP calls in tests mocked (do not make real GitHub requests in tests)

## Definition of done

- `pytest -q` passes at or above target count
- `agentkit hot --tweet-only` produces ≤280 char tweet with real content
- `./scripts/post-hot.sh --dry-run` prints tweet, exits 0
- All files committed to git (do not push)
- BUILD-REPORT.md written
