# All-Day Build Contract: agentkit-cli v1.6.0 handoff bundle

Status: In Progress
Date: 2026-04-20
Owner: OpenClaw subagent execution pass
Scope type: Deliverable-gated

## 1. Objective

Build a deterministic `agentkit bundle` workflow that packages the key repo-understanding artifacts into one coding-agent-ready handoff. The command should gather the canonical source context, source-audit findings, repo map, and contract-ready execution brief into a single markdown or JSON artifact with explicit gaps when upstream inputs are missing. The goal is to make the path real: source -> audit -> map -> contract -> bundle, so users can hand one coherent artifact to a coding agent instead of stitching the workflow together manually.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full relevant validation must pass at the end.
4. Docs and report surfaces must update in the same pass as code.
5. Output must be deterministic and schema-backed where JSON is offered.
6. Never modify files outside `/Users/mordecai/repos/agentkit-cli-v1.6.0-handoff-bundle`.
7. Commit after each completed deliverable, not only at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do not refactor unrelated command surfaces or reshape existing analyze/source/map/contract behavior beyond what this feature strictly needs.
10. Read the existing source, source-audit, map, and contract code/tests before writing new code.

## 3. Feature Deliverables

### D1. Deterministic bundle engine + schema

Add a narrow engine that assembles the existing repo-understanding surfaces into one explicit handoff bundle.

Required:
- `agentkit_cli/bundle.py` (new if needed)
- supporting schema/types
- any narrow helpers needed to reuse existing source/source-audit/map/contract logic

- [ ] Define a schema-backed result object for the bundle with stable JSON output
- [ ] Pull in canonical source context, source-audit findings, map summary, and contract/handoff content through existing deterministic paths where possible
- [ ] Represent missing upstream surfaces explicitly instead of silently skipping them
- [ ] Keep the bundle deterministic and local, with no model-generated synthesis requirement
- [ ] Add focused unit tests for bundle assembly

### D2. CLI workflow + portable artifact rendering

Expose the bundle as a first-class CLI command that creates a ready-to-share artifact for coding-agent handoff.

Required:
- `agentkit_cli/main.py`
- command module(s) and rendering helpers
- relevant docs/help surfaces

- [ ] Add `agentkit bundle <path>` (or an equivalently clear command) to the CLI
- [ ] Support human-readable markdown/text output plus `--json`
- [ ] Produce one coherent handoff structure with sections for source, audit, architecture, execution contract, and open gaps
- [ ] Keep output useful even when some upstream artifacts are missing by surfacing actionable gap notes
- [ ] Add focused CLI/help tests

### D3. Docs + workflow narrative + validation

Update the product story so the workflow becomes `source -> audit -> map -> contract -> bundle` instead of four disconnected primitives.

Required:
- `README.md`
- `CHANGELOG.md`
- `progress-log.md`
- `BUILD-REPORT.md` (and versioned report if this repo uses one for release-ready state)
- focused tests under `tests/`

- [ ] Update README quickstart and workflow sections to show the new bundle handoff
- [ ] Add an end-to-end test or fixture path covering a realistic bundled handoff artifact
- [ ] Run a focused validation slice covering source, audit, map, contract, and bundle behavior
- [ ] Leave the repo release-ready locally with docs and report surfaces aligned to actual branch state

## 4. Test Requirements

- [ ] Unit tests for each deliverable
- [ ] Integration coverage for a realistic source -> audit -> map -> contract -> bundle workflow
- [ ] Edge cases: canonical source missing, partial upstream availability, deterministic JSON output, and explicit gap rendering
- [ ] Existing related tests still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include what was built, what tests pass, what is next, and any blockers
- Before trusting any release/status narrative, run `scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.6.0-handoff-bundle` first, then run `scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.6.0-handoff-bundle`
- Before final summary, run `scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.6.0-handoff-bundle`
- Final summary only when all deliverables are done or a stop condition triggers

## 6. Stop Conditions

- All deliverables checked and validation passing -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write blocker report
- Scope creep detected, for example a general workflow orchestrator or live coding-agent execution runner -> STOP, report the new requirement, and keep the branch narrow
- If full bundle generation requires inventing new upstream semantics rather than assembling existing deterministic surfaces, cut scope to a clear composition layer and report the limit explicitly
