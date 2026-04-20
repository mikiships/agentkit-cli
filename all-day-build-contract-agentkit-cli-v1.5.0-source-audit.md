# All-Day Build Contract: agentkit-cli v1.5.0 source audit

Status: In Progress
Date: 2026-04-20
Owner: OpenClaw subagent execution pass
Scope type: Deliverable-gated

## 1. Objective

Build a deterministic `agentkit source-audit` workflow that checks the canonical source file or promoted legacy context file for missing sections, weak constraints, contradictory guidance, and contract-readiness gaps, then emits an actionable markdown and JSON report. The goal is to make the path real: source -> audit -> map -> contract, so users can tighten intent before they hand work to coding agents.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full relevant validation must pass at the end.
4. Docs and report surfaces must update in the same pass as code.
5. Output must be deterministic and schema-backed where JSON is offered.
6. Never modify files outside `/Users/mordecai/repos/agentkit-cli-v1.5.0-source-audit`.
7. Commit after each completed deliverable, not only at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do not refactor unrelated command surfaces or reshape existing analyze/map/contract behavior beyond what this feature strictly needs.
10. Read existing source, contract, and docs tests before writing new code.

## 3. Feature Deliverables

### D1. Deterministic source-audit engine + schema

Add a narrow engine that loads `.agentkit/source.md` when present, otherwise falls back to the best detected legacy context file, then scores structural quality for agent execution readiness.

Required:
- `agentkit_cli/source_audit.py` (new if needed)
- `agentkit_cli/commands/source_audit_cmd.py` or equivalent command wiring surface
- `agentkit_cli/main.py`

- [ ] Detect the canonical source path first, with explicit fallback behavior when only legacy files exist
- [ ] Check for concrete execution-critical sections such as objective, scope/boundaries, rules/constraints, validation/testing expectations, and expected deliverables or handoff structure
- [ ] Detect obvious contradictions or risky ambiguity patterns with deterministic heuristics, not freehand model output
- [ ] Define a schema-backed result object that supports stable JSON output
- [ ] Add focused unit tests for the audit engine

### D2. CLI workflow + actionable rendering

Expose the audit through a first-class CLI command with readable output for humans and machine-readable output for automation.

Required:
- `agentkit_cli/main.py`
- command module(s) and rendering helpers
- relevant docs/help surfaces

- [ ] Add `agentkit source-audit <path>` (or an equivalent clearly named command) to the CLI
- [ ] Support markdown/text-style human output plus `--json`
- [ ] Render concrete findings with severity, evidence, and suggested fixes instead of vague scores only
- [ ] Include a contract-readiness summary so the command naturally leads into `agentkit contract`
- [ ] Add focused CLI/help tests

### D3. Docs + workflow handoff + validation

Update the product story so the new workflow is explicit and tested end to end.

Required:
- `README.md`
- `CHANGELOG.md`
- `progress-log.md`
- `BUILD-REPORT.md` (and versioned report if this repo uses one for release-ready state)
- focused tests under `tests/`

- [ ] Update README quickstart and workflow sections to show `source -> source-audit -> map -> contract`
- [ ] Add an end-to-end test or fixture path covering a realistic source file with both good and bad findings
- [ ] Run a focused validation slice covering source, audit, contract, and map behavior
- [ ] Leave the repo release-ready locally with docs and report surfaces aligned to the actual branch state

## 4. Test Requirements

- [ ] Unit tests for each deliverable
- [ ] Integration coverage for a realistic source -> audit -> contract-oriented workflow
- [ ] Edge cases: canonical source missing, legacy fallback, contradictory duplicate guidance, missing validation section, and JSON output determinism
- [ ] Existing related tests still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include what was built, what tests pass, what is next, and any blockers
- Before trusting any release/status narrative, run `scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.5.0-source-audit` first, then run `scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.5.0-source-audit`
- Before final summary, run `scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.5.0-source-audit`
- Final summary only when all deliverables are done or a stop condition triggers

## 6. Stop Conditions

- All deliverables checked and validation passing -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write blocker report
- Scope creep detected, for example a full spec editor or LLM-driven auditing requirement -> STOP, report the new requirement, and keep the branch narrow
- If deterministic contradiction detection cannot be kept honest without broad natural-language inference, cut scope to structural readiness checks and report the limit explicitly
