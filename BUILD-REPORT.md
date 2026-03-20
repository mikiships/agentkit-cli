# BUILD-REPORT — agentkit-cli v0.66.0

**Build date:** 2026-03-20
**Feature:** `agentkit user-team`

## Deliverables

- [x] D1: `TeamScorecardEngine` in `agentkit_cli/user_team.py` — fetch org contributors, score each via UserScorecardEngine, aggregate team result
- [x] D2: `agentkit user-team` CLI command with `--limit/--json/--output/--share/--quiet` flags; wired into main.py
- [x] D3: `TeamScorecardHTMLRenderer` in `agentkit_cli/user_team_html.py` — dark-theme HTML with contributor rankings, grade distribution, top-scorer callout, avatars
- [x] D4: README updated (user-team section), CHANGELOG updated, version bumped 0.65.0→0.66.0

## Test Count

- **Baseline:** 3232 tests (v0.65.0)
- **New tests:** ≥38 (test_user_team_d1.py: 13, test_user_team_d2.py: 11, test_user_team_d3.py: 8, test_user_team_d4.py: 8)
- **Target total:** ≥3270

---

# BUILD-REPORT — agentkit-cli v0.65.0

**Build date:** 2026-03-19
**Feature:** `agentkit user-badge`

## Deliverables

- [x] D1: `UserBadgeEngine` in `agentkit_cli/user_badge.py` — badge URL generation, README markdown, anybadge JSON, score_to_badge_grade, inject_badge_into_readme
- [x] D2: `agentkit user-badge` CLI command with --score/--grade/--output/--share/--json/--inject/--dry-run flags
- [x] D3: `--inject` flag — idempotent sentinel-based README injection; --dry-run preview
- [x] D4: `--badge` flag on `agentkit user-scorecard` and `agentkit user-card`; badge_url added to JSON output
- [x] D5: README updated (User Badges section), CHANGELOG updated, version bumped 0.64.0→0.65.0

## Test Count

- **Baseline:** 3169 tests (v0.64.0)
- **New tests:** 41 (test_user_badge_d1.py: 22, test_user_badge_d2.py: 13, test_user_badge_d3.py: 10, test_user_badge_d4.py: 8, test_user_badge_d5.py: 9)
- **Target total:** ≥3209

## Example Badge URL

```
https://img.shields.io/badge/agent-readiness-A%20%2892%2F100%29-brightgreen?style=flat-square
```

## Summary

Implemented `agentkit user-badge` across 5 deliverables: a `UserBadgeEngine` class with shields.io badge URL generation, README markdown, and anybadge-compatible JSON; a `user-badge` CLI command with fast-mode `--score` flag, `--inject` for idempotent README updates using sentinel markers, and full `--json` output; `--badge` flags on both `user-scorecard` and `user-card` commands adding badge markdown to terminal output and `badge_url` to JSON payloads; and complete docs/changelog/version updates. All 41 new tests pass with zero regressions against the 3169 baseline tests.

DONE: v0.65.0 ready for release.
