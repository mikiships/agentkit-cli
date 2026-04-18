# RELEASE NEXT STEP, v0.98.0 mainline sync

## Source of truth
- Base branch: `origin/main`
- Shipped source branch/tag: `release/v0.98.0` / `v0.98.0`
- Scope to recover: optimize command + renderer + repo sweep flow, improve/run integration, release-check hardening, and only the docs/site updates needed to keep the shipped story and tests coherent.

## Import map
### Port directly
- `agentkit_cli/optimize.py`
- `agentkit_cli/renderers/optimize_renderer.py`
- `agentkit_cli/commands/optimize_cmd.py`
- `agentkit_cli/models.py`
- `agentkit_cli/commands/run_cmd.py`
- `agentkit_cli/commands/improve.py`
- `agentkit_cli/improve_engine.py`
- `agentkit_cli/release_check.py`
- `agentkit_cli/commands/release_check_cmd.py`
- `agentkit_cli/main.py`
- optimize and release-check tests/fixtures

### Reconcile carefully
- `README.md`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `BUILD-REPORT-v0.98.0.md`
- `agentkit_cli/site_engine.py`
- minimal generated docs pages under `docs/`

### Intentionally not porting
- unrelated generated site churn across the long `chore: update agentkit site [skip ci]` chain
- release-branch progress logs / handoff logs that are not part of shipped product behavior
- unrelated script tweaks in `scripts/post-hot.sh` and `scripts/post-spotlight.sh`
- files outside this worktree

## Strategy
1. Commit the D1 import plan and progress log first.
2. Cherry-pick the shipped release-check hardening commits onto `origin/main`, resolving only in-scope conflicts.
3. Cherry-pick the shipped optimize commits, including improve integration and fixture/test packs.
4. Reconcile the final v0.98.0 docs/site commit manually so only required README/build-report/site surfaces land, not stale generated noise.
5. Run targeted tests, then full pytest, then final hygiene/status checks that exist in this worktree.

## Verification notes
- The contract references `scripts/pre-action-recall.sh`, `scripts/check-status-conflicts.sh`, and `scripts/post-agent-hygiene-check.sh`, but those helper scripts are not present in this worktree on `origin/main`. I will use the repo-local test suite and git hygiene checks instead, and I will report that mismatch explicitly in the final handoff.
