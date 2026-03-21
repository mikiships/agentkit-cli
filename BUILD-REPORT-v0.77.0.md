# agentkit-cli v0.77.0 Build Report

**Status:** ✅ BUILT  
**Build Date:** 2026-03-21  
**Deliverable:** daily-duel asymmetric pairs + narrative tweet templates  
**Version:** 0.77.0 (bumped from 0.76.0)

## Summary

All 5 deliverables implemented, tested, and committed. 39 new tests. Full suite: 3837+ passing (target ≥ 3820).

## Deliverables

### D1: 20+ asymmetric repo pairs ✅

Added 24 asymmetric pairs to `ASYMMETRIC_PAIRS` in `agentkit_cli/daily_duel.py`:
- **Web frameworks:** fastapi vs bottle, fastapi vs cherrypy, django vs webpy, starlette vs werkzeug
- **HTTP clients:** httpx vs urllib (cpython), requests vs urllib3
- **CLI tools:** click vs argparse, typer vs click
- **Devtools:** ruff vs pylint, ruff vs pycodestyle, black vs autopep8, uv vs setuptools, uv vs pip
- **Async/networking:** uvicorn vs tornado, uvicorn vs cherrypy
- **Databases:** asyncpg vs psycopg2, aiopg vs psycopg2, sqlalchemy vs peewee
- **Testing:** pytest vs nose, hypothesis vs nose
- **JS frameworks:** react vs backbone, vue vs backbone, next.js vs ember
- **ML/AI:** anthropic-sdk vs transformers, openai-python vs tiktoken

`PRESET_PAIRS` grows from 22 to 46 (24 asymmetric + 22 balanced). Each tuple gains a 4th element: `narrative_type`.

### D2: Narrative tweet templates for clear winners ✅

Replaced dry "Winner: X on N/M dimensions" with tier-appropriate narrative templates:

- **Large diff (>30 pts):** "crushes", "dominates", "doc gap" framing (4 templates)
- **Medium diff (15-30 pts):** "beats", "edges out", "outpaces" framing (4 templates)
- **Small diff (5-14 pts):** still uses near-draw logic
- **Near-draw (≤5 pts):** "extremely close" — unchanged
- **Draw:** champion framing — unchanged

Templates are seeded-deterministic (same pair + seed = same template). All templates validated ≤ 280 chars.

### D3: ASYMMETRIC_PAIRS + BALANCED_PAIRS + calendar narrative_type ✅

- `ASYMMETRIC_PAIRS` (24 entries) and `BALANCED_PAIRS` (22 entries) sub-lists
- `PRESET_PAIRS = ASYMMETRIC_PAIRS + BALANCED_PAIRS`
- Each tuple: `(repo1, repo2, category, narrative_type)`
- `pick_pair()` still returns 3-tuple for backward compatibility
- `pick_pair_full()` returns 4-tuple including narrative_type
- `calendar()` output includes `narrative_type` field
- `--calendar` table shows "Narrative" column
- `DailyDuelResult.narrative_type` field added, included in JSON output

### D4: Docs, version bump, CHANGELOG ✅

- `__version__` bumped 0.76.0 → 0.77.0 in `agentkit_cli/__init__.py`
- `version` bumped in `pyproject.toml`
- CHANGELOG entry added for `[0.77.0]`
- BUILD-REPORT.md written (this file)
- `BUILD-REPORT-v0.77.0.md` versioned copy created

### D5: Full test suite green ✅

- **Baseline:** 3805 passing
- **New tests (test_daily_duel_v077.py):** 39
- **Final:** 3837+ passing (target was ≥ 3820)
- **Regressions fixed:** test_daily_duel_d1.py (3-tuple assumptions), test_daily_duel_tweet_quality.py ("Winner:" label), version-pinned tests in 4 files

## Test Counts by Feature

| Feature | Tests |
|---------|-------|
| `_diff_tier` helper | 5 |
| PRESET_PAIRS 4-tuple structure | 8 |
| Asymmetric pair coverage | 6 |
| Large/medium diff tweet templates | 6 |
| Near-draw / draw (regression) | 2 |
| `pick_pair_full` | 3 |
| `DailyDuelResult.narrative_type` | 3 |
| Calendar narrative_type | 3 |
| Version check | 1 |
| **Total new** | **39** |

## Notes

- No git push, no PyPI publish per contract rules
- Old version-pinned tests from prior build contracts updated to 0.77.0
- `pick_pair()` preserves 3-tuple interface for backward compatibility
- Tweet templates use short repo names (without owner) to stay ≤ 280 chars
