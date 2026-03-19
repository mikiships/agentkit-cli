# BUILD-REPORT.md — agentkit-cli v0.58.0

**Date:** 2026-03-19
**Version:** 0.58.0
**Baseline tests:** 2725 (v0.57.0)
**Final tests:** 2802 passed, 0 failed

---

## Feature Summary

v0.58.0 adds `agentkit pages-org` — a command that scores all public repos in a GitHub organization and publishes a dark-theme org-wide leaderboard to GitHub Pages.

The viral mechanic: one command gives any GitHub org a live, shareable AI-readiness scorecard at `https://<owner>.github.io/agentkit-scores/`.

---

## Deliverable Status

- [x] **D1** — `OrgPagesEngine` core (`agentkit_cli/engines/org_pages.py`)
  - Accepts org name + optional pages_repo, pages_path, pages_branch
  - Uses OrgCommand to score all public repos
  - Generates dark-theme responsive `index.html` + `leaderboard.json`
  - Handles git clone/pull/commit/push (mirrors daily_leaderboard.py pattern)
  - Returns `OrgPagesResult` dataclass
  - **28 tests** in `tests/test_org_pages_d1.py` ✅

- [x] **D2** — `agentkit pages-org` CLI command (`agentkit_cli/commands/pages_org_cmd.py`)
  - Full option set: --pages-repo, --pages-path, --pages-branch, --only-below, --limit, --json, --quiet, --dry-run
  - Rich progress bar + summary table
  - `--quiet` prints only final URL (cron-friendly)
  - **14 tests** in `tests/test_org_pages_d2.py` ✅

- [x] **D3** — `agentkit org --pages` flag integration
  - `--pages`, `--pages-repo`, `--dry-run` added to `agentkit org`
  - Invokes OrgPagesEngine after scoring, adds pages_url to JSON result
  - **11 tests** in `tests/test_org_pages_d3.py` ✅

- [x] **D4** — GitHub Actions workflow (`.github/workflows/examples/agentkit-org-pages.yml`)
  - Runs every Monday 8 AM UTC + workflow_dispatch
  - Setup guide in workflow comments
  - **16 tests** in `tests/test_org_pages_d4.py` ✅

- [x] **D5** — Docs, CHANGELOG, version bump, BUILD-REPORT
  - Version bumped: `0.57.0` → `0.58.0` in `pyproject.toml` + `agentkit_cli/__init__.py`
  - CHANGELOG: v0.58.0 entry added
  - README: "Publishing & Sharing" → "Org Leaderboard" section added
  - `docs/index.html`: "Org Leaderboard" nav entry + test count updated to 2780
  - Stale `0.57.0` version assertions updated in all affected test files
  - **10 tests** in `tests/test_org_pages_d5.py` ✅

---

## Test Count

| Phase | Tests |
|-------|-------|
| Baseline (v0.57.0) | 2725 |
| New tests (D1-D5) | +79 |
| **Final (v0.58.0)** | **2802** |

Target was ≥ 2780. Achieved 2802. ✅

---

## Validation

```
agentkit pages-org --help   # ✅ prints usage
agentkit org --help         # ✅ shows --pages flag
python3 -m pytest -q --tb=short 2>&1 | tail -3
# 2802 passed, 0 failed ✅
```

---

## Files Changed

### New files
- `agentkit_cli/engines/org_pages.py` — OrgPagesEngine core
- `agentkit_cli/commands/pages_org_cmd.py` — pages-org CLI command
- `.github/workflows/examples/agentkit-org-pages.yml` — GitHub Actions workflow
- `tests/test_org_pages_d1.py` — 28 tests
- `tests/test_org_pages_d2.py` — 14 tests
- `tests/test_org_pages_d3.py` — 11 tests
- `tests/test_org_pages_d4.py` — 16 tests
- `tests/test_org_pages_d5.py` — 10 tests

### Modified files
- `agentkit_cli/__init__.py` — version bump
- `agentkit_cli/main.py` — pages-org command + org --pages flag
- `agentkit_cli/commands/org_cmd.py` — --pages/--pages-repo/--dry-run flags
- `pyproject.toml` — version bump
- `CHANGELOG.md` — v0.58.0 entry
- `README.md` — Org Leaderboard section
- `docs/index.html` — nav entry + test count
- `BUILD-REPORT.md` — this file
- Multiple test files — stale `0.57.0` → `0.58.0` version assertions
