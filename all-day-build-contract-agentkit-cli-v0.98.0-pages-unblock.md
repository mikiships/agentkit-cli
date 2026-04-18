# All-Day Build Contract: agentkit-cli v0.98.0 pages unblock

Status: In Progress
Date: 2026-04-18
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Unblock the already-built `v0.98.0` optimize sweep release by repairing the unrelated pages/docs/build-report failures that stopped the full suite from going green. The concrete outcome is: the current RC worktree keeps the optimize sweep feature intact, restores the tracked GitHub Pages surface expected by tests, updates build reports with real final test counts, and ends with a green full suite so `v0.98.0` is release-ready locally.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. Do not push, tag, publish, or touch GitHub/PyPI.
5. Never modify files outside `/Users/mordecai/repos/agentkit-cli-rc-v0.97.2-optimize-unblock`.
6. Preserve the existing optimize sweep work. Do not rewrite or revert that feature.
7. Commit after each completed deliverable, not just at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do not absorb unrelated cleanup, refactors, or net-new features.
10. Read the failing tests and current docs/pages code before editing.
11. Summarize findings in prose in `progress-log.md`, never paste raw command output.
12. Treat this as a release unblock pass, not a redesign of the site.

## 3. Starting State

Current state in this RC worktree:
- Optimize sweep feature work is already present and targeted optimize/improve/run tests are green.
- Full suite is blocked by 11 failures outside optimize scope.
- Failing surfaces are concentrated in `docs/index.html` and build-report/test-count expectations.
- Repo has uncommitted release-prep files for `v0.98.0`; continue from the current state instead of starting over.

Known failing tests from the blocker report:
- `tests/test_daily_d5.py::TestBuildReport::test_build_report_mentions_test_count`
- `tests/test_pages_refresh.py::{test_has_fetch_script,test_has_render_function,test_has_recently_scored_section,test_has_repos_scored_stat_id,test_fetch_uses_agentkit_cli_path,test_renders_grade_classes,test_handles_fetch_error}`
- `tests/test_pages_sync_d4.py::{test_index_html_has_source_badge_css,test_index_html_has_community_scored_stat,test_index_html_has_repos_scored_stat_id}`

## 4. Feature Deliverables

### D1. Reconstruct the tracked pages surface

Required files as needed:
- `docs/index.html`
- `agentkit_cli/commands/pages_refresh.py`
- related page helpers only if the tests require a narrow fix

Restore the exact surface the pages tests expect without broad visual redesign.

- [ ] Read the failing pages tests first and map each expectation to the current missing surface
- [ ] Restore the `recently-scored` section, fetch/render script hooks, `repos-scored-stat` id, source-badge classes, and community-scored stat in the live docs surface
- [ ] Keep the page consistent with current dark-theme style instead of dropping in a test-only stub
- [ ] Add or adjust only the smallest code needed if JS/template helpers are out of sync with the HTML
- [ ] Run the targeted pages test files and get them green
- [ ] Commit D1 when the pages surface is green

### D2. Finalize build reports and release metadata

Required files:
- `BUILD-REPORT.md`
- `BUILD-REPORT-v0.98.0.md`
- `progress-log.md`
- other release-prep docs only if needed to reflect the final verified state

Make the release documentation truthful and test-backed.

- [ ] Update build reports with the real focused-test and final full-suite results for this RC
- [ ] Ensure `BUILD-REPORT.md` contains the final verified test count expected by the docs tests
- [ ] Record what was fixed in this unblock pass and why it was outside optimize scope
- [ ] Keep version metadata aligned with `0.98.0` unless a test proves otherwise
- [ ] Run the build-report docs test file and get it green
- [ ] Commit D2 when report/docs validation is green

### D3. Full-suite release unblock verification

Required files as needed:
- `README.md`
- `CHANGELOG.md`
- `agentkit_cli/__init__.py`
- `pyproject.toml`
- any touched release-prep file from the current RC state

Close the unblock pass by verifying the whole RC, not just the patched surfaces.

- [ ] Re-run the optimize targeted suite to confirm the original feature still passes after the unblock work
- [ ] Run the full suite and get it green
- [ ] Update `progress-log.md` with the final summary, including commit hashes and validation sequence
- [ ] Write a short final note in `BUILD-REPORT-v0.98.0.md` stating whether `v0.98.0` is release-ready locally
- [ ] Commit D3 only after the full suite is green

## 5. Test Requirements

Minimum required validation sequence:
- [ ] `uv run pytest -q tests/test_pages_refresh.py tests/test_pages_sync_d4.py tests/test_daily_d5.py`
- [ ] `uv run pytest -q tests/test_optimize_d1.py tests/test_optimize_d2.py tests/test_optimize_d3.py tests/test_optimize_d4.py tests/test_optimize_realworld.py tests/test_optimize_d2_hardening.py tests/test_optimize_smoke.py`
- [ ] `uv run pytest -q tests/test_improve.py tests/test_run.py tests/test_run_command.py`
- [ ] `uv run pytest -q`

Do not mark the contract complete unless all four gates pass.

## 6. Reports

- Update `progress-log.md` after each deliverable
- Include what was fixed, what tests pass, what remains, and any blocker
- Final summary must include: deliverables completed, commit hashes, targeted test results, full-suite result, and whether `v0.98.0` is release-ready locally

## 7. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write a blocker report
- Scope creep detected beyond pages/docs/report unblock work -> STOP and report it
- Any optimize sweep regression introduced by this pass -> STOP and document the regression precisely
