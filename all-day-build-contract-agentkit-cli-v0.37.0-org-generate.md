# All-Day Build Contract: agentkit-cli v0.37.0 — `agentkit org --generate`

Status: In Progress
Date: 2026-03-16
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Add a `--generate` flag to `agentkit org` that auto-generates CLAUDE.md files for every repo in the org (using agentmd), then re-scores each repo and shows the before/after score lift. This turns the audit from a read-only report into an actionable one-command fix.

The expected output format:
```
Before: pallets/flask  28.6/F
After:  pallets/flask  91.4/A  (+62.8 pts)
```

With `--generate --share`, the HTML report shows both columns (Before / After) side-by-side with the delta highlighted in green.

This is the viral mechanic: "one command to go from 0% agent-ready to 90%+."

## 2. Deliverables

### D1 — `--generate` flag on `agentkit org`
- `--generate` flag on the `org` command
- When set: after initial scoring, for each repo that scored < 80, run `agentmd generate .` in the cloned repo directory
- Re-run the full toolkit pipeline to get an "after" score
- Return both scores + delta per repo
- `--generate-only-below N` optional: only regenerate repos scoring below N (default 80)
- No side effects to remote repos (only local temp clones)

### D2 — Before/After display
- CLI table: add "Before" and "After" columns when `--generate` is active; drop "Score" + "Grade" in favor of side-by-side
- Color-coded delta column: green if improved ≥10pts, yellow if improved <10pts, red if degraded
- Summary line: "Generated context for X repos. Avg score lift: +Y pts"
- HTML report: two-column card layout showing before/after with color-coded delta badge

### D3 — `--generate-branch` flag (optional, bonus)
- If `--generate-branch <branch-name>` is passed along with `--generate`, create a new git branch in each temp clone, commit the CLAUDE.md, and print the diff as a summary
- Useful for users who want to see exactly what was generated without side effects
- This is a bonus deliverable; do D1+D2+D4+D5 first

### D4 — Tests
- 45+ new tests in `tests/test_org.py` and `tests/test_org_generate.py`
- Mock agentmd generate calls for speed; test the before/after data structure and display logic
- Test the HTML before/after columns and delta badge rendering
- All 1391 existing tests must still pass

### D5 — Docs, version bump, BUILD-REPORT
- README: update `agentkit org` section with `--generate` flag documentation and example
- CHANGELOG: v0.37.0 entry
- `pyproject.toml` + `agentkit_cli/__init__.py`: 0.36.1 → 0.37.0
- `BUILD-REPORT.md` in repo root: status, deliverables checklist, test count

## 3. Validation Gates

All must pass before marking BUILT:
- [ ] `python3 -m pytest -q` — full suite passes (1391 + ≥45 new = ≥1436 total)
- [ ] `agentkit org github:mikiships --generate` runs end-to-end without error
- [ ] Before/after scores shown in CLI table
- [ ] `--share` with `--generate` produces HTML with before/after columns
- [ ] No remote writes to GitHub (temp-only clones)

## 4. Stop Conditions

STOP immediately if:
- D1+D2 deliverables are complete and tests pass — do not continue to D3 if time is tight
- Any test failure in the existing 1391 tests that you can't fix in ≤3 attempts
- Any remote write to GitHub repos (should be impossible since we're cloning to tmpdir)

## 5. Output

When done, write `BUILD-REPORT.md` to `~/repos/agentkit-cli/` with:
- Status: BUILT / RELEASE-READY
- Deliverables: checklist
- Test count: `pytest -q` final line
- Any known issues
- Do NOT push to PyPI or git — the build loop handles that.
