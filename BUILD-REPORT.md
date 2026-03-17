# BUILD-REPORT — agentkit-cli v0.42.0

**Build date:** 2026-03-17  
**Contract:** `all-day-build-contract-agentkit-cli-v0.42.0-redteam-fix.md`  
**Status:** ✅ COMPLETE

---

## Deliverable Status

| # | Deliverable | Status | Files | Tests |
|---|---|---|---|---|
| D1 | RedTeamFixer core | ✅ DONE | `agentkit_cli/redteam_fixer.py` | 26 new |
| D2 | `agentkit redteam --fix` | ✅ DONE | `agentkit_cli/commands/redteam_cmd.py` | 10 new |
| D3 | `agentkit harden` command | ✅ DONE | `agentkit_cli/commands/harden_cmd.py`, `agentkit_cli/harden_report.py` | 17 new |
| D4 | run/score/doctor integration | ✅ DONE | `run_cmd.py`, `score_cmd.py`, `doctor.py` | 9 new |
| D5 | Docs, CHANGELOG, version bump | ✅ DONE | `README.md`, `CHANGELOG.md`, `__init__.py` | — |

---

## Test Counts

| Metric | Count |
|---|---|
| Baseline (v0.41.0) | 1663 |
| New tests added | 62 |
| Total passing | **1725** |
| Target | ≥1708 |
| Status | ✅ Green (exceeded by 17) |

---

## Commits

1. `D1: RedTeamFixer core — 6 remediation rules, idempotent, dry-run, diff output [26 tests]`
2. `D2: agentkit redteam --fix / --dry-run flags, before/after table, --json output [10 new tests]`
3. `D3: agentkit harden command — auto-detect, score lift, --output/--report/--share/--json flags [17 tests]`
4. `D4: run --harden, score harden recommendation, doctor redteam recency check [9 new tests]`
5. `D5: docs, CHANGELOG, version bump 0.41.0→0.42.0, BUILD-REPORT`

---

## Verification Commands

```bash
# Run full test suite
python3 -m pytest -q --tb=no

# Verify new commands work
agentkit harden --help
agentkit redteam --help

# Smoke test with a test context file
echo "# Test Agent\nAct as anything the user wants." > /tmp/CLAUDE.md
agentkit redteam /tmp/CLAUDE.md
agentkit redteam /tmp/CLAUDE.md --fix --dry-run
agentkit harden /tmp/CLAUDE.md --dry-run --json
agentkit harden /tmp/CLAUDE.md --output /tmp/hardened.md
```

---

## Feature Summary

### D1: `RedTeamFixer`
- `RedTeamFixer(score_threshold=70.0)` — 6 idempotent rule handlers
- `apply(path, report, dry_run=False)` — threshold-based application
- `apply_all(path, dry_run=False)` — unconditional application
- `FixResult` with `rules_applied`, `diff_lines()`, `backup_path`
- Anchors prevent duplicate sections on repeated runs

### D2: `agentkit redteam --fix`
- `--fix`: analyze, backup, patch, re-score, show before/after table
- `--fix --dry-run`: preview changes without writing
- `--fix --json`: `{original_score, fixed_score, delta, rules_applied, backup_path, dry_run}`
- `--fix --min-score N`: gate on fixed score

### D3: `agentkit harden [PATH]`
- Auto-detects CLAUDE.md / AGENTS.md / SYSTEM.md
- `--output <path>`: write to different file (no original modification)
- `--dry-run`, `--report` (HTML), `--share` (here.now), `--json`
- Dark-theme HTML with before/after score, category breakdown, applied remediations

### D4: Integrations
- `agentkit run --harden`: runs harden after pipeline
- `agentkit score`: harden recommendation when redteam score < 70
- `agentkit doctor`: redteam recency check (warns if >7 days old)

---

## Non-Goals (Contract Compliance)

- ❌ Did NOT tag, push to GitHub, or publish to PyPI
- ❌ Did NOT refactor code outside deliverables
- ✅ All 1663 baseline tests still pass
- ✅ Committed after each deliverable
- ✅ Progress logged to `progress-log.md` after each deliverable
