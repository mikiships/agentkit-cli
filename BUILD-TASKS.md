# BUILD-TASKS.md — agentkit-cli v1.24.0 clean JSON stdout

- [x] Make `agentkit spec --json` emit pure JSON on stdout with no human preamble
- [x] Preserve human progress/reporting without polluting JSON mode, preferably via stderr or suppressed text
- [x] Add focused regression coverage for the broken `--json` contract
- [x] Reconcile local status surfaces truthfully after the fix and validation
- [x] Run focused validation plus a full-suite confidence pass
- [x] Commit the completed local build state
