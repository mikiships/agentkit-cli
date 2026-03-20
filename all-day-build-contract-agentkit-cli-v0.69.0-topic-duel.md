# All-Day Build Contract: agentkit topic-duel

Status: In Progress
Date: 2026-03-20
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Add `agentkit topic-duel <topic1> <topic2>` — head-to-head comparison of two GitHub topics by agent-readiness. Fetch top repos for each topic (via GitHub Search API), score them with agentkit's toolkit, produce a side-by-side ranked comparison with winner declaration per dimension. Output: Rich terminal table + dark-theme HTML report + `--share` to here.now.

This extends the existing `agentkit topic` and `agentkit duel` patterns. Viral mechanic: "Which ecosystem is more AI-agent-ready — fastapi or django? langchain or llamaindex?"

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end. Run: `python3 -m pytest -q`
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory (`~/repos/agentkit-cli/`).
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Baseline

- Current version: 0.68.0
- Test count: ~3401 passing (1 flaky in test_watch.py — skip that test if it blocks the suite)
- Target version: 0.69.0
- Reference implementations to study first:
  - `agentkit_cli/commands/topic.py` (v0.68.0 — topic ranking)
  - `agentkit_cli/commands/duel.py` (v0.30.0 — repo duel)
  - `agentkit_cli/commands/user_duel.py` (v0.61.0 — user duel)
  - `agentkit_cli/html/` (HTML renderer patterns)

## 4. Feature Deliverables

### D1. TopicDuelEngine core (`agentkit_cli/engines/topic_duel.py`)

Fetch top repos for each of two topics using GitHub Search API (same approach as TopicEngine in topic.py). Score each repo set with ToolAdapter. Compute per-dimension winners and aggregate scores.

Required files:
- `agentkit_cli/engines/topic_duel.py`

Required:
- [ ] `TopicDuelEngine` class
- [ ] Fetch top N repos per topic (default: 5, configurable via `--repos-per-topic`)
- [ ] Score each repo with ToolAdapter (same scoring stack as `agentkit topic`)
- [ ] Compute comparison: avg score per topic, score distribution, winner per metric (context_score, lint_score, redteam_score, composite)
- [ ] `TopicDuelResult` dataclass with both topic results + comparison summary
- [ ] At least 12 unit tests in `tests/test_topic_duel_d1.py` (mock GitHub API + ToolAdapter)

### D2. `agentkit topic-duel` CLI command (`agentkit_cli/commands/topic_duel.py`)

Wire up the engine as a CLI command.

Required files:
- `agentkit_cli/commands/topic_duel.py`
- Update `agentkit_cli/cli.py` to register `topic-duel` command

Required:
- [ ] `agentkit topic-duel <topic1> <topic2>` positional args
- [ ] `--repos-per-topic N` (default 5, max 10)
- [ ] `--json` flag: output structured JSON payload
- [ ] `--quiet` flag: suppress progress spinner
- [ ] Rich terminal output: two side-by-side topic summary panels + winner declaration row
- [ ] At least 10 tests in `tests/test_topic_duel_d2.py` (mock engine, test CLI wiring + output)

### D3. Dark-theme HTML report (`agentkit_cli/html/topic_duel_renderer.py`)

Following the same dark-theme pattern used by `duel.py`, `user_duel.py`, and `topic.py`.

Required files:
- `agentkit_cli/html/topic_duel_renderer.py`

Required:
- [ ] `render_topic_duel_html(result: TopicDuelResult) -> str`
- [ ] Dark-theme HTML (same palette as existing renderers: bg #0d1117, accent teal/blue)
- [ ] Two columns: topic1 repos ranked vs topic2 repos ranked
- [ ] Winner banner at top (e.g., "fastapi wins: 73 vs 61 avg score")
- [ ] Per-repo score rows with color coding (A=green, B=blue, C=yellow, F=red)
- [ ] At least 8 tests in `tests/test_topic_duel_d3.py` (test HTML output, winner logic)

### D4. `--share` integration and `--output` flag

Required:
- [ ] `--share` flag on `topic-duel`: publish HTML to here.now and print URL
- [ ] `--output FILE` flag: write HTML to local file
- [ ] Wire through SharePublisher (already exists in `agentkit_cli/share.py`)
- [ ] At least 8 tests in `tests/test_topic_duel_d4.py` (mock share, test URL output)

### D5. Docs, CHANGELOG, version bump, BUILD-REPORT

Required:
- [ ] README.md: add `agentkit topic-duel` to command reference (same section as `agentkit topic`)
- [ ] CHANGELOG.md: v0.69.0 entry
- [ ] `pyproject.toml`: version bump `0.68.0` → `0.69.0`
- [ ] `agentkit_cli/__init__.py`: version bump
- [ ] `BUILD-REPORT-v0.69.0.md` in repo root
- [ ] Full test suite passes: `python3 -m pytest -q` (skip flaky test_watch if needed with `@pytest.mark.skip`)
- [ ] At least 5 tests covering the above docs/version assertions

## 5. Test Requirements

- [ ] Unit tests for each deliverable (≥12, ≥10, ≥8, ≥8, ≥5 per D1-D5 = ≥43 new tests)
- [ ] All existing tests must still pass (current baseline: ~3401; the test_watch.py::TestChangeHandler::test_last_file_recorded test is flaky under full-suite runs — mark it `@pytest.mark.skip(reason="flaky under full-suite parallelism")` if it causes failures)
- [ ] Mock all GitHub API calls and ToolAdapter calls (no real network in tests)
- [ ] Final count target: ≥3444 passing

## 6. Reports

- Write progress to `progress-log-v0.69.0.md` after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 7. Stop Conditions

- All deliverables checked and all tests passing → DONE
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected → STOP, report what's new
- All tests passing but deliverables remain → continue to next deliverable

## 8. DO NOT

- Deploy to here.now or publish to PyPI (build-loop handles that)
- Create new GitHub repos or push to GitHub
- Modify files outside `~/repos/agentkit-cli/`
- Add dependencies beyond what's already in pyproject.toml
