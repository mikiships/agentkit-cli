# BUILD-REPORT — agentkit-cli v0.78.0

## Version Built
0.78.0

## Tests Passing
3907 (≥3888 target met)

## Deliverables

- **D1: ExistingStateScorer** — `agentkit_cli/existing_scorer.py`, 7 dimension scorers, 40+ tests
- **D2: Integration** — `analyze_existing()`, `RepoDuelEngine(existing=True)`, `DailyDuelEngine(existing=True)` default, `--existing` CLI flag
- **D3: Tweet output** — non-circular scores, tweet shows real winner (not 100/100 draw)
- **D4: Docs** — version bumped to 0.78.0, CHANGELOG updated, BUILD-REPORT written, README updated

## What Was Built

v0.78.0 fixes the circular scoring problem in `agentkit daily-duel` by introducing `ExistingStateScorer` — a new module that measures a repo's documentation quality based on observable, pre-existing artifacts without triggering agentmd generation. The scorer evaluates seven dimensions: agent-context files (CLAUDE.md/AGENTS.md/llms.txt), README quality (length, sections, code examples, install instructions), CONTRIBUTING.md presence, CHANGELOG presence, CI config, test coverage, and type annotations. `DailyDuelEngine` now defaults to `existing=True`, so today's ruff vs pylint pair produces a real score difference instead of a 100/100 draw. The `--existing` flag is wired through `agentkit daily-duel`, `agentkit duel`, `RepoDuelEngine`, and a new `analyze_existing()` function in `analyze.py`.

## Issues Encountered

None. The main complexity was ensuring backwards compatibility: `RepoDuelEngine.existing` defaults to `False` (preserving old behavior) while `DailyDuelEngine.existing` defaults to `True` (the new desired default). All 62 new tests pass.

## Verification

```
$ agentkit daily-duel --tweet-only
ruff (78/100) beats pylint (38/100) across 4/7 agent-readiness dimensions. Which one would you hand to an AI agent?
```

Score difference is real — not "both score 100/100". ruff wins on agent_context, readme_quality, test_coverage, and type_annotations dimensions.
