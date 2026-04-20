# All-Day Build Contract: agentkit-cli v1.3.0 map

Status: In Progress
Date: 2026-04-19
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentkit map`, a deterministic repo-architecture mapper for local or GitHub targets. The command should turn a codebase into an agent-ready map of modules, entrypoints, scripts, tests, likely subsystem boundaries, and concrete next-task hints so Josh can move from vague "figure this repo out" to a usable explorer artifact in one command. This is the right next move because current signal is converging on specs, task decomposition, and explorer-first workflows, while agentkit already owns source and contract generation but still lacks the missing repo-map step between "analyze a repo" and "write a build contract."

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable, not only at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or improve unrelated code.
10. Read existing command patterns, tests, and README command sections before writing new code.
11. Keep the feature offline-safe for local targets. GitHub targets may clone/fetch through existing analyze/search helpers, but the final map generation must work entirely from the checked-out repo contents.
12. Reuse existing agentkit conventions for Rich tables, markdown reports, JSON output, and site/report helpers where they already fit.

## 3. Feature Deliverables

### D1. Core map engine + schema

Build a deterministic repo-mapping engine that inspects a local checkout and emits a stable structured representation of the repo.

Required:
- `agentkit_cli/map_engine.py`
- `agentkit_cli/models.py` or a new schema module if a cleaner home exists
- targeted fixtures under `tests/fixtures/`

- [ ] Define a schema for the map output, including repo summary, languages, important paths, entrypoints, scripts, tests, subsystem candidates, and task hints
- [ ] Implement a core engine that walks the repo safely, ignores junk/noise directories, and computes deterministic results
- [ ] Support local path input first-class
- [ ] Tests for D1

### D2. `agentkit map` CLI command

Add a first-class command that renders the repo map as readable markdown or Rich output and can also emit JSON for downstream tooling.

Required:
- `agentkit_cli/commands/map_cmd.py`
- `agentkit_cli/main.py`
- tests in `tests/test_map*.py`

- [ ] Add `agentkit map <target>` CLI wiring
- [ ] Support `--json`, `--output`, and `--format markdown|json|text` or an equivalent deterministic interface
- [ ] Support local targets and GitHub shorthand targets if that can be done by reusing existing safe repo-resolution helpers without introducing auth surprises
- [ ] Render a readable explorer-style summary with sections for architecture, entrypoints, scripts, tests, and likely build surfaces
- [ ] Tests for D2

### D3. Explorer-grade hints and task boundaries

Make the output actually useful for agent work, not just a fancy tree dump.

Required:
- `agentkit_cli/map_engine.py`
- `agentkit_cli/commands/map_cmd.py`
- tests covering behavior on realistic fixtures

- [ ] Infer subsystem boundaries or work lanes from directory structure, tooling files, and test layout
- [ ] Emit concrete "next tasks" or "likely work surfaces" grounded in the repo structure
- [ ] Flag risky or missing surfaces that matter for agents, for example missing tests near core code, missing context files, or scripts without obvious docs
- [ ] Keep heuristics deterministic and explainable, no hidden LLM dependency
- [ ] Tests for D3

### D4. Contract integration surface

Connect the new mapping feature to the newer source/contract workflow so it compounds instead of living as an orphan command.

Required:
- contract-related command or helper module where integration belongs
- README/examples updates showing the flow
- tests for integration behavior

- [ ] Add an integration path so `agentkit map` output can feed contract creation, either via a saved markdown artifact, structured JSON, or a documented `map -> contract` workflow
- [ ] If a light-touch `agentkit contract --from-map <file>` or equivalent fits cleanly, implement it; otherwise document and test the supported manual handoff path explicitly
- [ ] Keep scope bounded: do not redesign the contract system, just make the bridge real
- [ ] Tests for D4

### D5. Docs, reports, and release surfaces

Finish the feature like a real ship candidate.

Required:
- `README.md`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- version metadata files already used by the repo
- `progress-log.md`

- [ ] Document `agentkit map` purpose, CLI usage, and one concrete local + one GitHub example
- [ ] Update changelog and version to `1.3.0`
- [ ] Refresh build report and progress log with truthful validation/results
- [ ] Leave the repo ready for a later release-completion pass, not a half-documented feature branch
- [ ] Tests for D5 where docs/examples require fixture-backed coverage

## 4. Test Requirements

- [ ] Unit tests for each deliverable
- [ ] Integration test covering `agentkit map` end-to-end on at least one realistic fixture repo
- [ ] Edge cases: empty or tiny repo, monorepo-ish multi-dir layout, junk directories ignored, missing tests, script-heavy repo, local path with spaces
- [ ] All existing tests must still pass
- [ ] Final full suite passes under the repo's supported environment

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include what was built, what tests pass, what is next, and any blockers
- Before trusting any release/status narrative, run `scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.3.0-map` first, then run `scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.3.0-map` or an equivalent contradiction scan
- Before final summary or release claims, run `scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.3.0-map`
- Final summary only when all deliverables are done or the work stops on a real blocker

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP and write blocker report
- Scope creep detected, for example needing a whole new planner or graph engine -> STOP and report the newly discovered scope
- All tests passing but deliverables remain -> continue
