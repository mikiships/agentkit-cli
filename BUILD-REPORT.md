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
