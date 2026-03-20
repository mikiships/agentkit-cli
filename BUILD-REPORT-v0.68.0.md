# BUILD REPORT — agentkit-cli v0.68.0

**Date:** 2026-03-20
**Feature:** `agentkit topic <topic>` — rank top GitHub repos for a topic by agent-readiness
**Baseline:** v0.67.0 (3330 tests passing)

## Deliverables

### D1: TopicRankEngine (`agentkit_cli/topic_rank.py`) ✅
- `search_topic_repos(topic, limit, language)` — GitHub Search API, sort by stars, max 25 repos
- `TopicRankEntry` dataclass: rank, repo_full_name, score, grade, stars, description
- `TopicRankResult` dataclass: topic, entries, generated_at, total_analyzed, to_dict()
- `TopicRankEngine.run(topic, limit, language, progress_cb)` — fetch repos, score via analyze pipeline (heuristic fallback), rank by score desc
- 24 tests in `tests/test_topic_rank_d1.py` ✅

### D2: CLI command (`agentkit_cli/commands/topic_rank_cmd.py`) ✅
- `agentkit topic <topic>` registered in `main.py`
- Options: `--limit N` (default 10, max 25), `--language LANG`, `--share`, `--json`, `--output FILE`, `--quiet`
- Rich table: Rank | Repo | Score | Grade | Stars | Description (truncated to 40 chars)
- 10 tests in `tests/test_topic_rank_d2.py` ✅

### D3: HTML renderer (`agentkit_cli/topic_rank_html.py`) ✅
- `TopicRankHTMLRenderer.render(result)` — dark-theme HTML report
- Hero header with topic name and badge count
- Ranked table with grade color badges, star counts, descriptions
- Grade distribution bar chart (matches user-rank style)
- Top-repo spotlight card
- 14 tests in `tests/test_topic_rank_d3.py` ✅

### D4: Integration ✅
- `agentkit run --topic-repos <topic>` — runs topic-rank after pipeline
- Drill-down hint in `agentkit trending --topic <topic>` output
- 7 tests in `tests/test_topic_rank_d4.py` ✅

### D5: Docs, version, CHANGELOG ✅
- README: `agentkit topic` section added under Discovery & Benchmarking
- CHANGELOG: `## [0.68.0] - 2026-03-20` entry with full feature list
- `__version__` bumped to `"0.68.0"` in `agentkit_cli/__init__.py`
- `pyproject.toml` version bumped to `"0.68.0"`
- 7 tests in `tests/test_topic_rank_d5.py` ✅

## Test Results

| File | Tests |
|------|-------|
| test_topic_rank_d1.py | 24 |
| test_topic_rank_d2.py | 10 |
| test_topic_rank_d3.py | 14 |
| test_topic_rank_d4.py | 7 |
| test_topic_rank_d5.py | 7 |
| **Total new** | **62** |
| **Baseline** | 3330 |
| **Target total** | ≥3378 |
| **Actual total** | 3392 |

## Files Changed

- `agentkit_cli/__init__.py` — version bump
- `agentkit_cli/topic_rank.py` — new (TopicRankEngine)
- `agentkit_cli/topic_rank_html.py` — new (TopicRankHTMLRenderer)
- `agentkit_cli/commands/topic_rank_cmd.py` — new (CLI command)
- `agentkit_cli/main.py` — register `topic` command, add `--topic-repos` to `run`
- `agentkit_cli/commands/trending_cmd.py` — drill-down hint
- `pyproject.toml` — version bump
- `CHANGELOG.md` — 0.68.0 entry
- `README.md` — `agentkit topic` section
- `tests/test_topic_rank_d1.py` — 24 new tests
- `tests/test_topic_rank_d2.py` — 10 new tests
- `tests/test_topic_rank_d3.py` — 14 new tests
- `tests/test_topic_rank_d4.py` — 7 new tests
- `tests/test_topic_rank_d5.py` — 7 new tests
