# Progress Log — agentkit-cli v1.25.0 spec grounding shipped chronology

Status: SHIPPED
Date: 2026-04-21

## Why this lane exists

Heartbeat found a concrete CLI contract bug in the shipped repo: `agentkit spec --json` prepends `Wrote spec directory: ...` to stdout before the JSON object, which breaks direct machine parsing.

## Root cause

`agentkit_cli/commands/spec_cmd.py` always echoed the spec-directory write notice to stdout, even in JSON mode.

## What changed

- Routed the `Wrote spec directory: ...` notice to stderr when the effective format is JSON.
- Kept the notice on stdout for non-JSON runs.
- Added regression coverage for `spec --output-dir --json` so stdout must remain parseable JSON while stderr still carries the human notice.

## Validation

- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py` -> `8 passed in 9.20s`
- Direct command-path parse proof succeeded:
  - `uv run python -m agentkit_cli.main spec . --output-dir "$tmpdir/specdir" --json > "$tmpdir/spec.json" 2> "$tmpdir/spec.stderr"`
  - `json.loads(Path("$tmpdir/spec.json").read_text())` succeeded
  - stderr contained `Wrote spec directory: ...`
- `uv run python -m pytest -q` -> `5004 passed, 1 warning in 565.34s (0:09:25)`

## Local closeout truth

This lane is `RELEASE-READY (LOCAL-ONLY)`.

## Release-completion rerun

- Re-grounded the dirty partial-release tree instead of trusting the abandoned finisher state.
- Re-ran `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.24.0-json-clean-stdout` -> no contradictory success/blocker narratives found.
- Re-ran `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py` -> `8 passed in 0.94s`.
- Re-proved the direct stdout/stderr contract from the current tree: JSON parsed cleanly from stdout, and stderr carried `Wrote spec directory: ...`.
- Re-ran `uv run python -m pytest -q` -> `5004 passed, 1 warning in 196.61s (0:03:16)`.
- Re-ran `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.24.0-json-clean-stdout` -> `Total findings: 0`.
- Current truth before any irreversible step: `v1.24.0` is release-ready from this tree, but not shipped until push, tag, and PyPI are directly proven.

## 2026-04-21 release completion result: push, tag, publish, and verification succeeded

**Remote mutation that succeeded:**
- `git push -u origin feat/v1.24.0-json-clean-stdout` -> new remote branch `origin/feat/v1.24.0-json-clean-stdout` at `6790e96`
- `git tag -a v1.24.0 -m "agentkit-cli v1.24.0"` -> tag object `1f86c6593ba308bf004ac67cacb3e35ddaa9ebbe`, peel `6790e964cfb654fef87e7cbae55695aeb3e268ea`
- `git push origin v1.24.0` -> remote annotated tag now present and peeling to `6790e96`

**Publish proof:**
- `uv build` produced `dist/agentkit_cli-1.24.0-py3-none-any.whl` and `dist/agentkit_cli-1.24.0.tar.gz`
- `uvx twine upload --skip-existing dist/agentkit_cli-1.24.0.tar.gz dist/agentkit_cli-1.24.0-py3-none-any.whl` completed successfully

**Registry verification after publish:**
- `https://pypi.org/pypi/agentkit-cli/1.24.0/json` -> `info.version=1.24.0`, files: `agentkit_cli-1.24.0-py3-none-any.whl`, `agentkit_cli-1.24.0.tar.gz`
- `https://pypi.org/pypi/agentkit-cli/json` -> `info.version=1.24.0`, same two artifacts live after propagation
- `https://pypi.org/project/agentkit-cli/1.24.0/` -> HTTP `200` at the exact version page, though non-browser fetches still receive PyPI's client-challenge HTML

**Current truth:**
- `agentkit-cli v1.24.0` is shipped.
- The tested shipped commit is still tag target `6790e96`; any later branch-head commit remains chronology-only.

## 2026-04-21 v1.25.0 spec grounding — Deliverable D1 complete

### What was built
- Added stale-self-hosting regression coverage in `tests/test_spec_cmd.py` and `tests/test_spec_workflow.py`.
- Pinned the flagship failure mode where canonical source readiness and shipped workflow artifacts already prove the self-hosting prerequisite is done, but `agentkit spec` still recycles that old objective.
- Defined the planner evidence required to suppress the stale recommendation: canonical `.agentkit/source.md`, `source-audit` ready without fallback, shipped/local-ready workflow artifacts, and explicit `source -> audit -> map -> spec -> contract` lane evidence.

### Tests passing
- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py` -> `10 passed in 2.06s`

### Next
- Ground planner ranking in current repo truth and upgrade the emitted recommendation and contract seed so the flagship repo points at the honest adjacent build.

### Blockers
- None.

## 2026-04-21 v1.25.0 spec grounding — Deliverables D2 and D3 complete

### What was built
- Added planner grounding in `agentkit_cli/spec_engine.py` for flagship stale-objective cases where source-readiness and shipped workflow evidence already satisfy the old prerequisite.
- Introduced an `adjacent-grounding` recommendation that points the repo at improving `agentkit spec` itself when current repo truth shows the self-hosting/source-readiness work is already done.
- Upgraded the emitted why-now, scope, validation, evidence, and contract-seed fields so markdown and JSON output explain the honest next increment instead of falling back to the generic subsystem recommendation.
- Reproduced the flagship repo truth locally and verified `agentkit spec . --json` now returns `adjacent-grounding` with a contract seed focused on spec grounding.

### Tests passing
- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `18 passed in 1.10s`

### Next
- Update build/report surfaces for `v1.25.0`, run the required conflict and hygiene checks, then close out with full-suite truth.

### Blockers
- None.

## 2026-04-21 v1.25.0 spec grounding — Deliverable D4 complete

### What was built
- Updated `BUILD-REPORT.md`, added `BUILD-REPORT-v1.25.0.md`, and rewrote `FINAL-SUMMARY.md` for truthful local closeout.
- Added the `v1.25.0` changelog entry and bumped local version surfaces in `pyproject.toml` and `agentkit_cli/__init__.py`.
- Updated `tests/test_main.py` so the version flag matches the new local version surface.
- Re-ran the repo truth checks required by contract, including conflict detection, full-suite validation, and post-agent hygiene.

### Tests passing
- `uv run python -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `24 passed in 4.85s`
- `uv run python -m pytest -q` -> `5006 passed, 1 warning in 762.73s (0:12:42)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.25.0-spec-grounding` -> `No contradictory success/blocker narratives found.`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.25.0-spec-grounding` -> `Total findings: 0`

### Next
- None. This pass is `RELEASE-READY (LOCAL-ONLY)`.

### Blockers
- None.

## 2026-04-21 v1.25.0 release completion — Deliverable D1 complete

### Re-grounded release-ready truth
- Ran `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.25.0-spec-grounding` before any irreversible release step.
- Ran `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.25.0-spec-grounding` from the current tree.
- Re-checked repo truth directly instead of trusting prior summaries: branch `feat/v1.25.0-spec-grounding`, head `ecf1f46`, remote `origin`, and no existing `v1.25.0` tag.
- Noted current tree noise before release work: modified `BUILD-REPORT.md`, plus untracked contract files for this lane.

### Result
- Current truth is still `RELEASE-READY (LOCAL-ONLY)` pending fresh validation, branch push, tag, and PyPI publish proof.

### Blockers
- None.

## 2026-04-21 v1.25.0 release completion — Deliverable D2 complete

### Validation rerun from the release tree
- `uv run python -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `24 passed in 9.80s`
- Direct command-path proof from the current tree confirmed `uv run python -m agentkit_cli.main spec . --json` returns `primary_recommendation.kind=adjacent-grounding`.
- `uv run python -m pytest -q` -> `5006 passed, 1 warning in 863.10s (0:14:23)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.25.0-spec-grounding` -> `Total findings: 0`

### Result
- The current release tree still validates cleanly and is ready for irreversible release steps.

### Blockers
- None.

## 2026-04-21 v1.25.0 release completion — Deliverables D3 and D4 complete

### Remote mutation that succeeded
- `git push -u origin feat/v1.25.0-spec-grounding` -> remote branch created for the lane, and the later chronology reconciliation push advanced `origin/feat/v1.25.0-spec-grounding` to docs-only head `035ce8a`
- `git tag -a v1.25.0 -m "agentkit-cli v1.25.0" ecf1f46` -> annotated tag `v1.25.0` now peels to tested release commit `ecf1f46`
- `git push origin v1.25.0` -> remote annotated tag now present on origin

### Publish proof
- Built from detached release commit `ecf1f46`: `uv build` produced `dist/agentkit_cli-1.25.0-py3-none-any.whl` and `dist/agentkit_cli-1.25.0.tar.gz`
- `uvx twine upload --skip-existing dist/agentkit_cli-1.25.0.tar.gz dist/agentkit_cli-1.25.0-py3-none-any.whl` completed successfully

### Registry verification after publish
- `https://pypi.org/pypi/agentkit-cli/1.25.0/json` -> `info.version=1.25.0`, files: `agentkit_cli-1.25.0-py3-none-any.whl`, `agentkit_cli-1.25.0.tar.gz`
- `https://pypi.org/pypi/agentkit-cli/json` -> `info.version=1.25.0`, same two artifacts live after propagation
- `https://pypi.org/project/agentkit-cli/1.25.0/` -> HTTP `200` at the exact version page

### Current truth
- `agentkit-cli v1.25.0` is shipped.
- The tested shipped commit is tag target `ecf1f46`; later branch head `035ce8a` remains docs-only chronology.
- The flagship repo now self-specs the honest next adjacent build instead of recycling the already-satisfied self-hosting/source-readiness objective.

### Blockers
- None.
