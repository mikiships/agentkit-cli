# All-Day Build Contract: agentkit-cli v1.24.0 release completion

Status: In Progress
Date: 2026-04-21
Owner: OpenClaw release-completion pass
Scope type: Deliverable-gated

## 1. Objective

Take the already-built `agentkit-cli v1.24.0 clean JSON stdout` lane from truthful `RELEASE-READY (LOCAL-ONLY)` to fully shipped truth, or stop with an exact blocker report.

Current verified parent truth:
- Repo: `/Users/mordecai/repos/agentkit-cli-v1.24.0-json-clean-stdout`
- Branch: `feat/v1.24.0-json-clean-stdout`
- Last completed local-build commit: `39486dd` (`fix: keep spec json stdout clean`)
- The previous release finisher died mid-pass and left a dirty but informative worktree.
- Current dirty surfaces show an in-progress release attempt, not a finished ship:
  - version files bumped to `1.24.0` (`agentkit_cli/__init__.py`, `pyproject.toml`, `uv.lock`, `tests/test_main.py`)
  - `CHANGELOG.md` has a `1.24.0` entry
  - `.agentkit/source.md` was updated to point local report surfaces at `BUILD-REPORT-v1.24.0.md`
  - untracked release artifacts exist: `.release-check/`, `BUILD-REPORT-v1.24.0.md`, `all-day-build-contract-agentkit-cli-v1.24.0-release.md`
- `v1.23.0` remains the last shipped line until the four release surfaces below are directly proven for `v1.24.0`

This contract is complete only when all four release surfaces are directly proven and the repo/workspace chronology surfaces reflect one coherent `v1.24.0` shipped story.

## 2. Non-Negotiable Rules

1. No time-based completion claims.
2. No product-scope drift. This is release completion only.
3. Work only in `/Users/mordecai/repos/agentkit-cli-v1.24.0-json-clean-stdout` plus the explicitly named workspace memory files needed for chronology sync.
4. Completion is allowed only when every checklist item below is checked.
5. Keep shipped tag truth separate from any later docs-only chronology commit.
6. If blocked after 3 attempts on the same issue, stop and write the exact blocker.
7. No public-post drafting or outward messaging in this pass.

## 3. Deliverables

### D1. Ground the partial release state
- Re-run release recall for this repo before any irreversible step.
- Inspect the dirty worktree and decide what survives as truthful release state versus what should be reverted or regenerated.
- Re-run contradiction scan and fix any conflicting shipped vs local-only wording.
- Confirm the repo is truthfully release-ready before irreversible steps continue.

### D2. Validation from the release tree
- Re-run the focused JSON-stdout slice from the current tree.
- Re-run the full suite from the current tree.
- Re-run deterministic hygiene and resolve any non-intentional findings.

### D3. Four-surface release completion
- Push the release branch to origin.
- Create or verify annotated tag `v1.24.0` on the tested release commit.
- Push the tag to origin.
- Publish `agentkit-cli==1.24.0` to PyPI from this repo.
- Verify PyPI project page and version JSON both show `1.24.0` live with wheel and sdist.

### D4. Post-release chronology reconciliation
- Reconcile `BUILD-REPORT.md`, `BUILD-REPORT-v1.24.0.md`, `FINAL-SUMMARY.md`, and `progress-log.md` so they distinguish shipped tag truth from any later docs-only chronology head.
- Update `/Users/mordecai/.openclaw/workspace/memory/WORKING.md` so `last_shipped` and active-build state reflect shipped `v1.24.0` truth and the next slot is open.
- Update `/Users/mordecai/.openclaw/workspace/memory/temporal-facts.md` if it is used as a current shipped-truth surface for `agentkit-cli`.

## 4. Test Requirements

- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py`
- direct command-path proof that `agentkit spec --json` parses cleanly from stdout while the write notice lands in stderr
- `uv run python -m pytest -q`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.24.0-json-clean-stdout`
- PyPI project page and version JSON verified after publish

## 5. Reporting

- Append progress to `progress-log.md` after each completed deliverable.
- Before irreversible release steps, run `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.24.0-json-clean-stdout`.
- Run `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.24.0-json-clean-stdout` before irreversible steps and again after chronology reconciliation if needed.
- Final summary must say only one of two things: `SHIPPED` with the four surfaces proven, or `BLOCKED` with the exact blocker.

## 6. Stop Conditions

- All deliverables checked and four release surfaces proven -> DONE.
- 3 consecutive failed attempts on the same blocker -> STOP and write blocker report.
- If any irreversible step succeeds while later proof is ambiguous -> STOP, verify source-of-truth surfaces, then reconcile prose before doing anything else.
- If publish is blocked by auth, network, or registry failure that cannot be resolved safely in-pass -> STOP and write the exact blocker.
