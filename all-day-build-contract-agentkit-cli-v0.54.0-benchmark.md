# All-Day Build Contract: agentkit benchmark — Cross-Agent Benchmarking

Status: In Progress
Date: 2026-03-18
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Add `agentkit benchmark` command that runs a structured benchmark evaluating multiple AI agents (claude, codex, gemini) against the repo's actual codebase tasks. Produces a ranked comparison report showing which agent performs best on YOUR specific project, not on generic benchmarks they can game.

This command is the viral Show HN hook: "Benchmark Claude vs Codex vs Gemini on your own codebase in one command."

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Feature Deliverables

### D1. BenchmarkEngine core (agentkit_cli/benchmark.py)

Build the core benchmark engine. It runs a set of tasks against multiple agents using coderace under the hood (via ToolAdapter) and collects structured results.

Required files:
- `agentkit_cli/benchmark.py`

Required:
- [ ] `BenchmarkConfig` dataclass: agents list, tasks list, timeout, rounds
- [ ] `BenchmarkResult` dataclass: agent, task, score (0-100), duration_s, error
- [ ] `BenchmarkReport` dataclass: project, timestamp, results list, summary stats, winner
- [ ] `BenchmarkEngine` class with `run(project_path, config) -> BenchmarkReport`
- [ ] Default task set: 5 built-in tasks from coderace (bug-hunt, refactor, concurrent-queue, api-client, and a new "context-use" task that tests if the agent reads CLAUDE.md)
- [ ] Multi-agent execution (sequential per task, rounds support for statistical confidence)
- [ ] Per-agent aggregate stats: mean score, mean duration, win rate
- [ ] JSON-serializable output
- [ ] Tests: ≥15 tests in tests/test_benchmark_d1.py (mock coderace subprocess calls)

### D2. `agentkit benchmark` CLI command

Wire the engine into the Typer CLI.

Required files:
- Add `benchmark` command to `agentkit_cli/main.py`

Required:
- [ ] `agentkit benchmark [PATH]` (default: current dir)
- [ ] `--agents claude,codex,gemini` (comma-separated, default: auto-detect from agentkit doctor)
- [ ] `--tasks bug-hunt,refactor` (comma-separated, default: all 5)
- [ ] `--rounds N` (default: 1; 3+ for statistical confidence)
- [ ] `--timeout SECONDS` (default: 300)
- [ ] `--json` — emit JSON to stdout
- [ ] `--output FILE` — save report to file
- [ ] `--share` — publish dark-theme HTML to here.now
- [ ] `--quiet` — minimal output
- [ ] Rich progress display during runs (which agent, which task, scores as they come in)
- [ ] Final ranked table: Agent | Tasks | Mean Score | Mean Time | Win Rate
- [ ] Tests: ≥12 tests in tests/test_benchmark_d2.py

### D3. Dark-theme HTML benchmark report (agentkit_cli/benchmark_report.py)

Shareable report showing the full benchmark results in dark-theme HTML.

Required files:
- `agentkit_cli/benchmark_report.py`

Required:
- [ ] `BenchmarkReportRenderer` class with `render(report: BenchmarkReport) -> str`
- [ ] Hero: "Agent Benchmark: [project]" with winner callout and crown emoji
- [ ] Per-task matrix table: rows = tasks, columns = agents, cells = score + duration
- [ ] Aggregate stats bar: winner, best score, fastest agent
- [ ] Color coding: green ≥80, yellow 50-79, red <50
- [ ] `--share` wires to here.now publish (reuse existing publish logic from share.py)
- [ ] Tests: ≥10 tests in tests/test_benchmark_d3.py

### D4. Integration with `agentkit run` and `agentkit score`

Add `--benchmark` flag to `agentkit run` that runs benchmark after standard analysis.
Add benchmark result to composite score as an optional fifth signal.

Required:
- [ ] `--benchmark` flag on `agentkit run` triggers BenchmarkEngine after toolkit analysis
- [ ] Benchmark result included in run JSON output under `benchmark_result` key
- [ ] `agentkit score` shows benchmark_score if present in last run data (optional, skip if missing)
- [ ] Integration tests: ≥8 tests in tests/test_benchmark_d4.py

### D5. Docs, CHANGELOG, version bump, BUILD-REPORT

Required:
- [ ] `README.md`: Add "Benchmark" section with `agentkit benchmark` example
- [ ] `CHANGELOG.md`: Entry for v0.54.0 with feature summary
- [ ] `pyproject.toml`: version bumped from 0.53.0 → 0.54.0
- [ ] `agentkit_cli/__init__.py`: `__version__` = "0.54.0"
- [ ] `BUILD-REPORT.md`: Updated with v0.54.0 entry
- [ ] All existing tests still passing (2470 baseline)
- [ ] New tests total ≥ 2470 + 45 = 2515
- [ ] Tests: ≥5 tests in tests/test_benchmark_d5.py (version assertions, docs checks)

## 4. Validation Gates

Before marking complete:

```bash
# Full test suite must pass
python3 -m pytest -q --tb=short
# Benchmark command exists and shows help
python3 -m agentkit_cli benchmark --help
# Version string correct
python3 -c "import agentkit_cli; assert agentkit_cli.__version__ == '0.54.0'"
# Core module importable
python3 -c "from agentkit_cli.benchmark import BenchmarkEngine, BenchmarkReport"
```

## 5. Stop Conditions

Stop and write a blocker report if:
- The test suite drops below 2470 after your changes
- coderace subprocess interaction can't be reliably mocked
- Rich display causes test interference
- Any deliverable is blocked for 3+ attempts

## 6. Out of Scope

- Do NOT build an actual AI agent harness (no calling OpenAI/Anthropic APIs directly)
- The benchmark uses coderace as the evaluator — coderace already knows how to run agents
- Do NOT modify any files outside ~/repos/agentkit-cli
- Do NOT deploy to PyPI or here.now
- Do NOT add new dependencies beyond what's already in pyproject.toml

## 7. Expected Test Count

- D1: 15 new tests
- D2: 12 new tests
- D3: 10 new tests
- D4: 8 new tests
- D5: 5 new tests
- Total new: 50
- Final total: ≥2520 tests
