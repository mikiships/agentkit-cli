# All-Day Build Contract: agentkit-cli v1.23.0 release completion

Status: In Progress
Date: 2026-04-21
Owner: OpenClaw release-completion pass
Scope type: Deliverable-gated

## 1. Objective

Finish the partially completed `agentkit-cli v1.23.0` release from the current real state, without redoing already-proven irreversible steps and without lying about shipped status.

Current verified parent truth:
- Repo: `/Users/mordecai/repos/agentkit-cli-v1.23.0-self-spec-source`
- Branch: `feat/v1.23.0-self-spec-source`
- HEAD: `d6aceff` (`feat: self-host spec source readiness`)
- Remote branch already exists at the same commit.
- Annotated tag `v1.23.0` already exists locally and on origin, peeling to `d6aceff`.
- PyPI `agentkit-cli/1.23.0` is **not** live yet. Latest live PyPI version is still `1.22.0`.
- Working tree is not clean because `progress-log.md` is modified and the release contract file is untracked.

This contract is complete only when the repo is truthfully either:
1. `SHIPPED` with all four release surfaces directly proven, or
2. `BLOCKED` with the exact blocker documented and no ambiguous shipped prose.

## 2. Non-Negotiable Rules

1. No product-scope drift. This is release completion and chronology cleanup only.
2. Do not recreate or move the existing `v1.23.0` tag unless source-of-truth evidence proves it is wrong.
3. Keep shipped tag truth separate from any later docs-only chronology commit.
4. Work only in `/Users/mordecai/repos/agentkit-cli-v1.23.0-self-spec-source` plus the explicitly named workspace memory files needed for chronology sync.
5. Completion is allowed only when every checklist item below is checked.
6. If blocked after 3 attempts on the same issue, stop and write the exact blocker.
7. No public-post drafting or outward messaging in this pass.

## 3. Deliverables

### D1. Pre-release truth sweep
- Run release recall for this repo before any irreversible step.
- Run contradiction scan and fix any conflicting shipped vs local-only wording.
- Confirm the repo is still based on the intended tested release commit and that the existing remote tag/branch match that truth.
- Ground the modified `progress-log.md` state. Keep the repo truthful.

### D2. Validation from the release tree
- Re-run the focused self-spec/source/spec slice from the current tree.
- Re-run the full suite from the current tree.
- Re-run deterministic hygiene and resolve any non-intentional findings.
- If validation proves the current release commit is not trustworthy, stop and document the blocker instead of pushing ahead.

### D3. Complete the missing release surface
- Publish `agentkit-cli==1.23.0` to PyPI from this repo.
- Verify PyPI version JSON is live for `1.23.0`.
- Verify the PyPI project page/latest metadata reflects `1.23.0`.
- Verify both wheel and sdist exist.

### D4. Post-release chronology reconciliation
- Reconcile `BUILD-REPORT.md`, `BUILD-REPORT-v1.23.0.md`, `FINAL-SUMMARY.md`, and `progress-log.md` so they distinguish shipped tag truth from any later docs-only chronology head.
- Update `/Users/mordecai/.openclaw/workspace/memory/WORKING.md` so `last_shipped` reflects `v1.23.0` and the active-build slot is no longer falsely in progress.
- Update `/Users/mordecai/.openclaw/workspace/memory/temporal-facts.md` if it is used as a current shipped-truth surface for `agentkit-cli`.

## 4. Test Requirements

- `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.23.0-self-spec-source`
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.23.0-self-spec-source`
- `python3 -m agentkit_cli.main source-audit . --json`
- `python3 -m agentkit_cli.main spec . --output-dir <temp-dir> --json`
- `python3 -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py tests/test_daily_d5.py`
- `uv run python -m pytest -q`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.23.0-self-spec-source`
- PyPI project page and version JSON verified after publish

## 5. Reporting

- Append progress to `progress-log.md` after each completed deliverable.
- Before irreversible release steps, run `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.23.0-self-spec-source`.
- Run `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.23.0-self-spec-source` before irreversible steps and again after chronology reconciliation if needed.
- Final summary must say only one of two things: `SHIPPED` with the four surfaces proven, or `BLOCKED` with the exact blocker.

## 6. Stop Conditions

- All deliverables checked and all four release surfaces proven -> DONE.
- 3 consecutive failed attempts on the same blocker -> STOP and write blocker report.
- If any irreversible step succeeds while later proof is ambiguous -> STOP, verify source-of-truth surfaces, then reconcile prose before doing anything else.
- If publish is blocked by auth, network, registry, or credentials that cannot be resolved safely in-pass -> STOP and write the exact blocker.
