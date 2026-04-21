# BUILD-TASKS.md — agentkit-cli v1.24.0 clean JSON stdout

- [ ] Make `agentkit spec --json` emit pure JSON on stdout with no human preamble
- [ ] Preserve human progress/reporting without polluting JSON mode, preferably via stderr or suppressed text
- [ ] Add focused regression coverage for the broken `--json` contract
- [ ] Reconcile local status surfaces truthfully after the fix and validation
- [ ] Run focused validation plus a full-suite confidence pass
- [ ] Commit the completed local build state
