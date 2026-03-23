# All-Day Build Contract: agentkit-cli v0.93.0 — `agentkit changelog`

Status: In Progress
Date: 2026-03-23
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Add `agentkit changelog` command that generates an AI-produced changelog from git commits + quality score deltas, formatted for GitHub releases and PR descriptions. This closes the gap between "run quality analysis" and "communicate what changed to maintainers and users."

The command reads git log (since last tag or a specified ref), pairs it with agentkit quality score history from the SQLite DB, and produces: a human-readable changelog section, a score-delta summary, and optionally a GitHub release body or PR description.

This is the missing piece in the `agentkit run → agentkit gate → agentkit release-check` CI workflow: after you've verified the release is good, you still need to write the changelog.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (`python3 -m pytest -q` in repo root, ≥0 regressions from v0.92.0 baseline of ~1814 passing).
4. New features must ship with docs and CHANGELOG entry.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory (`~/repos/agentkit-cli/`).
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Feature Deliverables

### D1: ChangelogEngine core (≥12 tests)

File: `agentkit_cli/changelog_engine.py`

ChangelogEngine class with:
- `from_git(since: str | None, path: str)` — parse git log since a ref (default: last tag). Returns list of CommitSummary(hash, message, files_changed, author, ts).
- `from_history(project: str | None, since_days: int, db_path: str | None)` — read agentkit history DB, find score delta (current score - score N days ago). Returns ScoreDelta(before, after, delta, project).
- `render_markdown(commits, score_delta, version: str | None)` — produce clean markdown changelog section. Groups commits by conventional-commit prefix (feat/fix/chore/test/docs/refactor) if detected, otherwise uses "Changes" catch-all. Includes score-delta line if available.
- `render_release(commits, score_delta, version: str | None)` — same as render_markdown but formatted for GitHub release body (adds pip install command at end, removes chore/test entries by default).
- Graceful handling when git not available, no commits found, or history DB missing.

### D2: `agentkit changelog` CLI command (≥10 tests)

File: `agentkit_cli/commands/changelog_cmd.py`

```
agentkit changelog [OPTIONS]
```

Options:
- `--since TEXT` — git ref or tag to use as baseline (default: last tag or HEAD~10 if no tags)
- `--version TEXT` — version string to include in header (e.g. "v0.93.0")
- `--format [markdown|release|json]` — output format (default: markdown)
- `--output FILE` — write to file instead of stdout
- `--score-delta` — include quality score delta from history DB (default: on)
- `--no-chore` — exclude chore/test/ci commits from output
- `--project TEXT` — project path for score delta lookup (default: auto-detect from cwd)
- `--github-release` — short alias for --format release

Wire into `agentkit_cli/main.py` as `changelog` command.

### D3: Integration with `agentkit release-check` (≥5 tests)

Add `--changelog` flag to `agentkit release-check`:
- When `--changelog` is passed, run the changelog command at the end of release-check
- Append changelog content to release-check output
- Add `changelog_preview` key to `--json` output

This makes the full release workflow: `agentkit release-check --changelog` → prints test/git/tag/registry status + auto-generated changelog.

### D4: `GITHUB_STEP_SUMMARY` support + GitHub Release creation (≥8 tests)

File: `agentkit_cli/changelog_engine.py` (additions)

- When `GITHUB_STEP_SUMMARY` env var is set and `--format release` is used, append changelog to GitHub step summary
- `agentkit changelog --create-release` — create a GitHub release using `gh release create` CLI (only when `--version` is set and `--create-release` is passed). Writes release body from render_release(). Do NOT auto-run — requires explicit flag.

Tests should cover the GITHUB_STEP_SUMMARY path (mock env var), not actual GH API calls.

### D5: Docs, CHANGELOG, version bump to v0.93.0, BUILD-REPORT (≥5 tests)

- Add `## [0.93.0]` section to CHANGELOG.md
- Add `## Changelog Generation` section to README.md with usage examples
- Bump `__version__` in `agentkit_cli/__init__.py` to `0.93.0`
- Bump `version` in `pyproject.toml` to `0.93.0`
- Write `BUILD-REPORT.md` with: version, deliverables checked, test counts (baseline → final), any deviations
- Update version assertions in `tests/test_interactive_ui_d5.py` (change "0.92.0" → "0.93.0") — this file always needs updating on version bumps

## 4. Test Requirements

- Unit tests for each deliverable
- At least one integration test: run `agentkit changelog` against the agentkit-cli repo itself (uses real git, mock DB)
- Edge cases: no git history, no tags, history DB missing, empty commit list
- Full existing suite must still pass: `python3 -m pytest -q` ≥1814 passing, 0 regressions

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected → STOP, report what's new
- If git operations cause issues in test suite, mock them — do NOT modify git history

## 7. Success Criteria

1. `pytest -q` passes with ≥40 new tests, zero regressions from v0.92.0
2. `agentkit changelog` runs against the agentkit-cli repo and produces valid markdown
3. `agentkit release-check --changelog` produces a combined release check + changelog output
4. `agentkit changelog --format release --version v0.93.0` produces a GitHub release body
5. `git push + tag v0.93.0` complete
6. PyPI publish succeeds: `agentkit-cli 0.93.0` visible at https://pypi.org/project/agentkit-cli/0.93.0/
