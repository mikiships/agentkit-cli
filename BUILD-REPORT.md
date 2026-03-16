# BUILD-REPORT: agentkit-cli v0.38.0

**Status:** BUILT

**Date:** 2026-03-16

---

## v0.38.0 — `agentkit pr`

### Deliverables

- [x] **D1 — Core `pr` command** (`agentkit_cli/commands/pr_cmd.py`)
  - `agentkit pr github:<owner>/<repo>` clones repo (depth 1), runs `agentmd generate .`, checks for existing file
  - `--dry-run`, `--force`, `--file`, `--pr-title`, `--pr-body-file`, `--json` flags
  - Skips if context file already exists (unless `--force`)

- [x] **D2 — GitHub fork + branch + PR flow**
  - Checks/creates fork via GitHub API (`POST /repos/{owner}/{repo}/forks`)
  - Creates branch `agentkit/add-claude-md` on fork
  - Commits generated file, pushes to fork
  - Opens PR via `POST /repos/{owner}/{repo}/pulls`
  - Requires `GITHUB_TOKEN` (clear error if missing)
  - PR body from `agentkit_cli/templates/pr_body.md`

- [x] **D3 — Output + UX**
  - Rich progress steps: Clone → Generate → Fork → Branch → Commit → Push → PR
  - Success: prints PR URL
  - `--json`: `{"pr_url": ..., "repo": ..., "file": ..., "score_before": ..., "score_after": ...}`
  - Clear error messages for missing token, fork failure, network errors

- [x] **D4 — Tests** (`tests/test_pr_cmd.py`)
  - 30 new tests covering: dry-run, skip/force, missing token, JSON output, PR body template, branch name, fork creation, custom title, custom body file

- [x] **D5 — Docs + release prep**
  - `agentkit_cli/templates/pr_body.md` — PR body template
  - README: new `agentkit pr` section with full usage example
  - CHANGELOG: v0.38.0 entry
  - `pyproject.toml` version bump: 0.37.0 → 0.38.0
  - `agentkit_cli/__init__.py` version bump

### Test Results

- Baseline: 1441 tests
- New: 30 tests
- Final: **1471 tests passing** ✓

---

# BUILD-REPORT: agentkit-cli v0.37.0

**Status:** BUILT

**Date:** 2026-03-16

---

## Deliverables Checklist

- [x] **D1 — `--generate` flag on `agentkit org`**
  - `--generate` flag added to CLI and `OrgCommand`
  - `_generate_for_repo()` helper: clones to temp dir, runs `agentmd generate`, re-scores, returns before/after dict
  - `--generate-only-below N` flag (default: 80) — skips repos at or above threshold
  - `generate_summary` in JSON output: `generated_count` and `avg_score_lift`
  - No remote writes — all generation in local temp clones

- [x] **D2 — Before/After display**
  - CLI table shows Before / After / Delta columns (replaces Score / Grade) when `--generate` is active
  - Color-coded delta: green ≥10pts, yellow <10pts improvement, red ≤0pts
  - Summary line: "Generated context for X repos. Avg score lift: +Y pts"
  - `OrgReport` accepts `generate_mode=True` — renders Before / After / Delta columns with CSS delta badges
  - `--share` with `--generate` produces HTML with before/after columns

- [ ] **D3 — `--generate-branch` flag** *(optional bonus — not implemented, D1+D2+D4+D5 complete)*

- [x] **D4 — Tests**
  - 50 new tests in `tests/test_org_generate.py`
  - Covers: flag wiring, `_generate_for_repo` logic, before/after data structure, CLI table display, delta color coding, HTML before/after columns, JSON output with `generate_summary`, threshold enforcement
  - All 1391 existing tests still pass

- [x] **D5 — Docs, version bump, BUILD-REPORT**
  - `agentkit_cli/__init__.py`: 0.36.1 → 0.37.0
  - `pyproject.toml`: 0.36.1 → 0.37.0
  - `CHANGELOG.md`: v0.37.0 entry added
  - `README.md`: `agentkit org` section updated with `--generate` flag docs and example
  - `BUILD-REPORT.md`: this file

---

## Test Count

```
1441 passed, 1 warning in 27.00s
```

- Existing: 1391
- New (test_org_generate.py): 50
- Total: **1441**

---

## Files Changed

- `agentkit_cli/__init__.py` — version bump
- `pyproject.toml` — version bump
- `agentkit_cli/commands/org_cmd.py` — `--generate` flag, `_generate_for_repo()`, updated `OrgCommand`, updated `_render_table`
- `agentkit_cli/org_report.py` — `generate_mode` parameter, before/after HTML columns, delta CSS badges
- `agentkit_cli/main.py` — `--generate` and `--generate-only-below` Typer options on `org` command
- `CHANGELOG.md` — v0.37.0 entry
- `README.md` — `--generate` docs
- `tests/test_org_generate.py` — 50 new tests

---

## Known Issues

None. All validation gates pass:
- Full test suite: 1441 passed
- Before/after scores shown in CLI table when `--generate` is active
- `--share` with `--generate` produces HTML with before/after columns
- No remote writes to GitHub (temp-only clones via `tempfile.mkdtemp`)

---

Do NOT push to git or PyPI — build loop handles that.
