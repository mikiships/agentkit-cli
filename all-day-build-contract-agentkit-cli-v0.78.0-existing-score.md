# Build Contract: agentkit-cli v0.78.0 — Existing-State Scoring

## Problem
Daily-duel always returns 100/100 draws because the scoring pipeline is circular:
1. agentmd **generates** a CLAUDE.md from the repo
2. agentlint validates the **generated** file
3. Result: always passes because generated content is always valid

This makes daily-duel useless as an organic content source and misleading as a quality metric.

## Goal
Add an "existing-state" scoring mode that measures a repo's documentation quality **before** any generation. This produces real score differences between modern well-documented repos and older/sparser ones.

## Scope
- Modify `agentkit analyze` and `agentkit duel` / `agentkit daily-duel` to support `--existing` mode (skip agentmd generation, score what's already there)
- Add `ExistingStateScorer` class that scores repos based on observable facts:
  - Presence of CLAUDE.md, AGENTS.md, or llms.txt (binary, high weight)
  - README quality: length, has sections, has code examples, has install instructions
  - Has CONTRIBUTING.md or CONTRIBUTING/ directory
  - Has CHANGELOG or CHANGELOG.md or HISTORY.md  
  - Has CI config (.github/workflows/*.yml, .travis.yml, etc.)
  - Test coverage: presence of tests/ directory + rough test count
  - Has type annotations (py.typed marker or stub files)
  - Docs site link in README (pyproject.toml or setup.py docs_url)
- Make `agentkit daily-duel` default to `--existing` mode (no agentmd pre-generation)
- Make `agentkit duel` support `--existing` flag
- Update tweet generation to reflect real score differences

## Deliverables

### D1: ExistingStateScorer (≥18 tests)
- `agentkit_cli/existing_scorer.py`
- Analyzes cloned repo directory for documentation artifacts
- Returns dict of dimension scores (0-100) and composite
- Must score pylint < ruff on at least 2 dimensions (verify this in tests with fixtures)

### D2: Integration into analyze and duel (≥12 tests)
- Add `--existing` flag to `agentkit analyze`
- Add `--existing` flag to `agentkit duel` 
- Add `--existing` flag to `agentkit daily-duel` and make it **the default**
- When `--existing` is used, skip agentmd generation step, use ExistingStateScorer instead

### D3: Better tweet text for clear winners (≥8 tests)
- In `daily_duel.py` `_build_tweet_text()`: add template variants for asymmetric pairs with >5pt difference
- Template examples:
  - "ruff (97/100) vs pylint (71/100): ruff wins on {winning_dims} dimensions. Modern Python devtools: agent-ready by design."
  - "pytest (95/100) vs nose (42/100): pytest wins decisively. nose hasn't had active maintenance since 2016 — and agent readiness shows it."
- Must verify tweet text is NOT "both score 100/100" for ruff vs pylint in tests

### D4: Docs, tests, version bump (≥5 tests)
- Bump `__version__` to 0.78.0 in `agentkit_cli/__init__.py`
- Update CHANGELOG.md with entry
- Write BUILD-REPORT.md at `~/repos/agentkit-cli/BUILD-REPORT.md`
- Update README.md with `--existing` flag documentation

## Test Targets
- Baseline: **3845** tests
- New target: **≥3888** tests (≥43 new)
- All tests must pass: `python3 -m pytest -q`

## Stop Conditions
- DO NOT change the PyPI publish step (build-loop handles that)
- DO NOT modify cron definitions  
- DO NOT run `openclaw` CLI commands
- DO NOT deploy to here.now
- DO NOT run `agentkit publish` or `agentkit share`
- Commit all changes locally with `git add -A && git commit -m "feat: v0.78.0 existing-state scoring"`

## Verification (builder must verify before done)
1. `python3 -m pytest -q` → all tests pass, ≥3888 total
2. `agentkit daily-duel --tweet-only` → output is NOT "both score 100/100" for today's pair (ruff vs pylint)
3. `agentkit daily-duel --tweet-only` → shows a real score difference
4. `git log --oneline -5` → commit exists

## Contract End
When done, write BUILD-REPORT.md to ~/repos/agentkit-cli/BUILD-REPORT.md with:
- Version built
- Tests passing count
- What was built (one paragraph)
- Any issues encountered
- Verification results (paste the actual daily-duel --tweet-only output)
