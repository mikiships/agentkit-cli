# All-Day Build Contract: agentkit-cli v1.8.0 clarify loop

Status: In Progress
Date: 2026-04-20
Owner: OpenClaw subagent execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build a deterministic `agentkit clarify` workflow that surfaces the exact unresolved questions and assumption gates before a coding agent starts executing a taskpack. The current lane now reaches `source -> source-audit -> map -> contract -> bundle -> taskpack`, but users still have to manually notice ambiguities, contradictions, or missing decisions before handing the packet to Codex or Claude Code. This pass should remove that manual reasoning step by generating a stable clarification packet with prioritized questions, assumption flags, and explicit go/no-go guidance.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside `/Users/mordecai/repos/agentkit-cli-v1.8.0-clarify-loop`.
7. Commit after each completed deliverable, not only at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do not refactor or restyle unrelated code.
10. Read existing source-audit, contract, bundle, taskpack, and CLI tests/docs before writing new code.

## 3. Feature Deliverables

### D1. Deterministic clarify engine + schema

Add a first-class clarify engine that consumes taskpack-ready surfaces and emits a stable clarification model. The model should separate blocking questions from softer follow-ups, record the evidence for each question, and explicitly mark whether execution should proceed, proceed-with-assumptions, or pause.

Required:
- `agentkit_cli/clarify.py`
- any supporting schema/helpers needed for stable clarify rendering
- tests covering deterministic structure and ordering

- [ ] Implement deterministic clarify assembly from existing source-audit, contract, bundle, and taskpack surfaces
- [ ] Include explicit sections for blocking questions, follow-up questions, assumptions, contradictions, and execution recommendation
- [ ] Support stable JSON output with schema-backed keys and deterministic ordering
- [ ] Tests for D1

### D2. CLI workflow + actionable rendering

Expose the new workflow through the CLI so a user can generate a clarification brief before sending work to a coding agent. The CLI should support human-readable markdown, JSON, and output-file flows without manual glue.

Required:
- `agentkit_cli/commands/clarify_cmd.py`
- CLI wiring in main/help surfaces
- tests for text/JSON/output-file flows

- [ ] Add `agentkit clarify <path>` CLI entrypoint
- [ ] Support rendering that is concise but actionable for a human or upstream orchestrator
- [ ] Support writing clarification artifacts to disk in markdown and JSON forms
- [ ] Tests for D2

### D3. End-to-end ambiguity loop validation

Prove the full `source -> audit -> map -> contract -> bundle -> taskpack -> clarify` lane works and fails clearly when prereqs are missing or contradictory.

Required:
- focused end-to-end workflow tests
- contradiction / missing-surface coverage
- docs/report updates for the new lane

- [ ] Add focused end-to-end tests for the full workflow including clarify
- [ ] Add gap-path tests for missing upstream artifacts or contradictory inputs
- [ ] Update README, changelog, and build-report/progress surfaces for `1.8.0`
- [ ] Tests for D3

### D4. Release-readiness pass

Leave the worktree in a truthful local release-ready state, not partially updated. Version metadata, changelog, docs, build report, and progress log must all agree.

Required:
- `pyproject.toml`
- `agentkit_cli/__init__.py`
- `uv.lock`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.8.0.md`
- `progress-log.md`

- [ ] Bump release metadata to `1.8.0`
- [ ] Reconcile docs and report surfaces to one local release-ready story
- [ ] Run contradiction + hygiene checks on the final repo state
- [ ] Tests/checks for D4

## 4. Test Requirements

- [ ] Unit tests for clarify engine and renderers
- [ ] CLI tests for human-readable and JSON/output-file flows
- [ ] Integration test covering `source -> source-audit -> map -> contract -> bundle -> taskpack -> clarify`
- [ ] Edge cases: missing source, contradictory source/taskpack inputs, missing upstream artifacts, deterministic output ordering, correct execution recommendation levels
- [ ] All existing tests must still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include what was built, exact tests that passed, what remains, and any blockers
- Before trusting any release/status narrative, run:
  - `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.8.0-clarify-loop`
  - `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.8.0-clarify-loop`
- Before final summary, run:
  - `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.8.0-clarify-loop`
- Final summary when all deliverables are done or the pass stops

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write a blocker report
- Scope creep detected beyond clarification generation -> STOP and report the newly discovered requirement
- Any contradiction remains unresolved between tests and report surfaces -> STOP until source-of-truth state is reconciled
