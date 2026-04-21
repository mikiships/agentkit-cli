# All-Day Build Contract: agentkit-cli v1.23.0 self-spec source readiness

Status: Complete
Date: 2026-04-21
Owner: OpenClaw build loop
Scope type: Deliverable-gated

## 1. Objective

Make the flagship `agentkit-cli` repo pass its own source-audit and spec flow cleanly.

Current trigger from the shipped `v1.22.0` repo state:
- `agentkit spec /Users/mordecai/repos/agentkit-cli-v1.22.0-spec` blocked immediately
- `agentkit source-audit` reported 4 blocker findings on the repo source surface:
  - missing scope guidance
  - missing constraints guidance
  - missing validation guidance
  - missing deliverables guidance
- audit also warned that the repo still falls back to legacy `AGENTS.md` because `.agentkit/source.md` is missing

This build is complete only when the repo has a canonical source file, `source-audit` is ready for contract, `spec` succeeds on the flagship repo, and the local build state is truthfully documented.

## 2. Scope

Work only in `/Users/mordecai/repos/agentkit-cli-v1.23.0-self-spec-source`.

In scope:
- canonical source promotion for this repo
- deterministic source content needed for self-hosted `source-audit` and `spec`
- tests, docs, and report surfaces required to make the new local truth explicit

Out of scope:
- remote push, tag, or PyPI publish
- unrelated feature work
- public-post drafting or launch work

## 3. Constraints

1. Keep this build narrowly about self-spec source readiness.
2. Do not edit files outside this worktree.
3. No release claims beyond truthful local state.
4. Keep outputs deterministic and aligned with existing `agentkit` command semantics.
5. If a command blocks on an environment issue rather than repo truth, note it explicitly and keep going where safe.
6. Commit after the local build is truly complete.

## 4. Deliverables

### D1. Canonical source promotion
- Create or promote `.agentkit/source.md` for this repo.
- Ensure the canonical source includes explicit objective, scope, constraints, validation, and deliverables sections.
- Remove ambiguity about whether later source-audit/spec steps should read legacy fallback content.

### D2. Self-spec flow success
- Make `agentkit source-audit` report ready-for-contract on this repo.
- Make `agentkit spec` succeed on this repo and emit a next-build recommendation instead of blocking.
- If command behavior needed code changes, add the necessary tests and docs.

### D3. Truthful local closeout
- Update `BUILD-REPORT.md`, `FINAL-SUMMARY.md`, and any version-specific report surface that this repo uses.
- Record the exact command outputs and key results in `progress-log.md`.
- Leave the repo in truthful local build-complete state with one final commit.

## 5. Validation

Required minimum checks:
- `agentkit source-audit /Users/mordecai/repos/agentkit-cli-v1.23.0-self-spec-source --json`
- `agentkit spec /Users/mordecai/repos/agentkit-cli-v1.23.0-self-spec-source --output-dir <temp-dir>`
- focused pytest slice covering source-audit/spec behavior
- full-suite confidence pass from the repo

Use the repo `.venv` binaries when present.

## 6. Reporting

- Append progress to `progress-log.md` after each completed deliverable.
- Final summary must say the repo is locally complete only if the validation gates actually passed.
- If blocked, stop with the exact blocker and the exact failing path.
