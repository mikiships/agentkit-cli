# Progress Log, v0.98.0 Mainline Sync

## D1. Source-of-truth map and import plan
- Read the build contract and current README.
- Compared `origin/main...release/v0.98.0` and mapped the shipped surfaces that matter for this sync.
- Confirmed the recoverable product scope is concentrated in release-check hardening, optimize command/repo-sweep support, improve/run wiring, tests/fixtures, and a final site/docs reconciliation commit.
- Explicitly excluded unrelated release-branch noise: long generated site refresh chains, extra progress logs, and unrelated posting-script changes.
- Verification: inspected the release-only file list, release-only commit list, and the main diffs for optimize/release-check/test surfaces.
- Environment note: the contract asks for helper scripts (`scripts/pre-action-recall.sh`, `scripts/check-status-conflicts.sh`, `scripts/post-agent-hygiene-check.sh`) that do not exist in this worktree, so final validation will rely on the available test suite plus git hygiene checks.

## Next
- Port release-check hardening first.
- Port optimize and improve/run integration next.
- Reconcile the minimal docs/site surfaces and then run full validation.
