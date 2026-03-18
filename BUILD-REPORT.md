# BUILD-REPORT: agentkit-cli v0.45.0 — `agentkit explain`

**Date:** 2026-03-18
**Version:** 0.45.0
**Feature:** LLM-powered coaching report explaining WHY scores are what they are

---

## Deliverables Checklist

| # | Deliverable | Status | File(s) |
|---|-------------|--------|---------|
| D1 | ExplainEngine — LLM coaching report engine | ✅ DONE | `agentkit_cli/explain.py` |
| D2 | `agentkit explain` CLI command | ✅ DONE | `agentkit_cli/commands/explain_cmd.py`, `agentkit_cli/main.py` |
| D3 | Template-based explanation quality | ✅ DONE | `agentkit_cli/explain.py` (`template_explain`) |
| D4 | `agentkit run --explain` integration | ✅ DONE | `agentkit_cli/commands/run_cmd.py`, `agentkit_cli/main.py` |
| D5 | Docs, CHANGELOG, version bump, BUILD-REPORT | ✅ DONE | `README.md`, `CHANGELOG.md`, `pyproject.toml`, `agentkit_cli/__init__.py`, `BUILD-REPORT.md` |

---

## D1: ExplainEngine (`agentkit_cli/explain.py`)

- `ExplainEngine(model, timeout)` — configurable LLM model and timeout
- `load_report(path)` — loads and validates JSON report file
- `build_prompt(report)` — builds concise (<2000 token) prompt with score, tier, findings, tool scores
- `call_llm(prompt)` — calls Anthropic API via `anthropic` SDK; graceful fallback on missing key, missing package, or API errors
- `template_explain(report)` — rule-based markdown coaching report, works offline with zero extra dependencies
- `explain(report)` — full pipeline: prompt → LLM (or template fallback) → markdown
- `explain_run_result(result)` — accepts RunResult dict directly for `--explain` integration

## D2: `agentkit explain` CLI

```
agentkit explain [PATH] [--report REPORT_JSON] [--model MODEL] [--no-llm] [--json] [--output FILE]
```

- `PATH` — optional project directory; runs inline analysis if no --report given
- `--report REPORT_JSON` — load from existing report JSON
- `--model MODEL` — LLM model (default: claude-3-5-haiku-20241022)
- `--no-llm` — force template mode, offline, no API key required
- `--json` — structured JSON output: project, score, tier, explanation, recommendations[], one_thing
- `--output FILE` — write markdown coaching report to file
- Rich console output with Panel header and Markdown rendering

## D3: Template-based explanation quality

Score tiers with distinct language:
- **A (≥90):** "Your repo is well-configured for AI agents. Here's what's already working..."
- **B (70-89):** "Good foundation with room to improve. The biggest opportunities are..."
- **C (50-69):** "Mixed results. AI agents can work here but will hit friction in..."
- **F (<50):** "Significant gaps found. Agents working on this repo will likely..."

Plain-language finding explanations for: path-rot, year-rot, bloat, script-rot, stale-todo, multi-file-conflict, mcp-security, and more.

## D4: `agentkit run --explain` integration

- `--explain` flag added to `agentkit run`
- `--no-llm` flag added to `agentkit run` (for offline coaching)
- After pipeline completes, calls `ExplainEngine.explain_run_result(summary)`
- Appends "## Coaching Report" section to console output
- If `--json`, includes `coaching_report` field in JSON payload

## D5: Docs and version

- `README.md`: "AI-Powered Explanations" section with usage examples
- `CHANGELOG.md`: v0.45.0 entry with full feature list
- `pyproject.toml`: bumped 0.44.0 → 0.45.0
- `agentkit_cli/__init__.py`: bumped 0.44.0 → 0.45.0
- `tests/test_explain.py`: all D1-D5 tests (≥40 tests)

---

## Test Coverage

Target: ≥1897 tests (baseline 1857 + 40 new)

| Deliverable | Min Tests | Actual |
|-------------|-----------|--------|
| D1 (ExplainEngine) | ≥12 | 15+ |
| D2 (explain_cmd) | ≥10 | 11+ |
| D3 (template quality) | ≥8 | 8+ |
| D4 (run --explain) | ≥6 | 6+ |
| D5 (docs/version) | ≥4 | 4+ |
| **Total** | **≥40** | **44+** |

---

## Distribution Angle

"Your AI agent's AI quality score, explained by AI." The meta-recursion is the hook.

The `agentkit explain` command positions agentkit-cli as the first agent quality tool with AI-powered self-explanation — a meaningful differentiator for Show HN and the AI tooling community.
