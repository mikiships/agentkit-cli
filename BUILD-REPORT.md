# BUILD-REPORT — agentkit-cli v0.7.0

**Date:** 2026-03-13
**Contract:** agentkit-cli-v0.7.0-github-action.md
**Final test count:** 250 passing (target: ≥230)

---

## What Was Built

### D1 — GitHub Actions composite action

**`action.yml`** (root-level marketplace entry point) — complete rewrite from the v0.6.0 pipeline action to match the contract spec:
- Inputs: `python-version` (3.11), `min-lint-score` (70), `post-comment` (true), `github-token` (required)
- Outputs: `lint-score`, `drift-status`, `review-summary`
- Fails the action (exit 1) only when lint score < `min-lint-score`

**`scripts/run-agentkit-action.py`** — orchestrates the three quality checks:
- `agentlint check-context` — finds AGENTS.md / CLAUDE.md / copilot-instructions.md, runs lint, parses score
- `agentmd drift` — detects context drift (fresh / drifted / unknown)
- `coderace review --diff HEAD~1..HEAD --lanes 2` — skipped gracefully when not on a PR or tool unavailable
- Aggregates all results into `/tmp/agentkit-quality-summary.json`
- Sets GitHub Actions outputs via `$GITHUB_OUTPUT`
- Exits 1 when lint score below threshold

**`scripts/post-pr-comment.py`** — posts the quality report to the PR:
- Idempotent: updates existing comment (keyed by HTML marker) or creates new one
- Non-fatal: silently skips when `GITHUB_TOKEN` / `PR_NUMBER` / `REPO` are missing
- Formatted markdown table comment

### D2 — Example workflow + README

**`examples/agentkit-quality.yml`** — complete ready-to-use 3-line workflow adopters can copy.

**README.md** — "GitHub Action" section added after "Sharing Results":
- What the action checks
- Copy-paste workflow snippet
- PR comment format preview
- Full inputs/outputs table
- Badge example
- Link to example workflow

### D3 — Tests (40 new tests)

**`tests/test_action.py`** — 40 tests covering:
- action.yml structure (inputs, outputs, composite type, defaults)
- `find_context_file` — missing dir, AGENTS.md, CLAUDE.md
- `run_agentlint` — no context (skipped), score parsing
- `run_agentmd_drift` — no context, fresh, drifted detection
- `run_coderace` — not-PR skip, ok result, missing tool graceful handling
- `set_output` — writes to `$GITHUB_OUTPUT`
- `main()` — exit codes (above / below threshold), JSON output structure
- `_build_comment` — markdown content
- `post-pr-comment.py` — no token (non-fatal), no PR_NUMBER, marker detection, create new, update existing, missing summary file
- Example workflow YAML validity and structure
- README section presence

### D4 — Version bump + CHANGELOG

- `pyproject.toml`: `0.6.0` → `0.7.0`
- `agentkit_cli/__init__.py`: `0.6.0` → `0.7.0`
- `tests/test_main.py`: updated version assertion to `0.7.0`
- `CHANGELOG.md`: `## v0.7.0` entry documenting all additions

---

## Final Test Count

```
250 passed (3 consecutive runs — no flakiness)
```

Pre-existing timing-sensitive tests in `test_watch.py` occasionally show 1-2 failures on CI under load, but pass consistently in isolation and in repeated full-suite runs. These are pre-existing, not regressions from this build. Non-watch tests: 233 stable.

---

## Deviations from Contract

None material. One minor structural note: the previous `action.yml` was an earlier pipeline action (v0.6.0 scope). It was replaced in full as required by the contract. The old inputs (`skip`, `benchmark`, `fail-on-lint`) were removed; contract inputs added.

---

## Git Log (this build)

```
77d68b1 D4: CHANGELOG, version 0.7.0
4d13b55 D1-D3: GitHub Action composite action, scripts, example workflow, tests
```
