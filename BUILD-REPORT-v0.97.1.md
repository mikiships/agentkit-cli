# BUILD-REPORT.md — agentkit-cli v0.97.1 optimize hardening

Date: 2026-04-18
Builder: scoped subagent
Contract: all-day-build-contract-agentkit-cli-v0.97.1-optimize-hardening.md

## Summary

Hardened `agentkit optimize` so it behaves more safely on realistic context files, preserves protected sections more reliably, avoids pointless rewrites on already-tight files, and composes more cleanly with the existing improve/run workflows.

This pass does not push, tag, or publish.

## Deliverables

| # | Deliverable | Status | Notes |
|---|-------------|--------|-------|
| D1 | Real-world fixture pack and failure mapping | ✅ Complete | Added four realistic fixture shapes plus second-pass idempotence coverage |
| D2 | Protected-section and no-op hardening | ✅ Complete | Added protected section tracking, low-signal cleanup, and deterministic no-op detection |
| D3 | Review UX and apply safety polish | ✅ Complete | Review output now reports verdicts/protected sections and skips no-op rewrites |
| D4 | Higher-level workflow hardening | ✅ Complete | Improve/run optimize integration now degrades cleanly when optimize fails |
| D5 | Docs, changelog, build report, version prep | ✅ Complete | README, CHANGELOG, BUILD-REPORT, and version metadata updated for 0.97.1 |

## Hardening Outcomes

- realistic optimize fixtures now cover bloated rules, already-tight context, risky instruction files, and mixed-signal documents
- protected headings now include identity, autonomy, user-critical, and safety-oriented sections
- low-signal sections such as scratchpads or request dumps now drop cleanly after risky-content cleanup instead of surviving as confusing stubs
- no-op results stay explicit and `--apply` no longer rewrites an effectively unchanged file
- improve/run integrations now preserve the parent workflow when optimize hits a bounded failure

## Remaining Caveats

- protected-section detection is still heading-based and intentionally conservative rather than semantic
- large diff output is truncated for review readability, so machine consumers should prefer `--json`

## Focused Test Results

- `pytest -q tests/test_optimize_d1.py tests/test_optimize_d2.py tests/test_optimize_d3.py tests/test_optimize_d4.py tests/test_optimize_realworld.py tests/test_optimize_d2_hardening.py tests/test_improve.py tests/test_run.py tests/test_run_command.py` -> `112 passed in 8.48s`

## Final Validation

- Full suite target size at validation time: `4750` collected tests
- `pytest -q` -> `4750 passed, 1 warning in 393.37s (0:06:33)`
