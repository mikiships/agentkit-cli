# BUILD-REPORT.md — agentkit-cli v1.23.0 release completion

Status: BLOCKED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.23.0-release.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Re-ran release truth sweep from `d6aceff` and confirmed no contradictory success or blocker narratives. |
| D2 | ✅ Complete | Re-ran the focused self-spec slice, full suite, and hygiene checks from the current tree. |
| D3 | ⚠️ Blocked | Branch push and annotated tag succeeded, but PyPI publish failed on missing credentials for `https://upload.pypi.org/legacy/`. |
| D4 | ✅ Complete | Repo and workspace chronology surfaces now record the blocked release truth instead of implying ship. |

## Validation

- `python3 -m agentkit_cli.main source-audit . --json` -> `ready_for_contract: true`, `blocker_count: 0`, `used_fallback: false`
- `python3 -m agentkit_cli.main spec . --output-dir <temp-dir> --json` -> succeeded and wrote deterministic artifacts
- `python3 -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py tests/test_daily_d5.py` -> `34 passed in 1.47s`
- `uv run python -m pytest -q` -> `5003 passed, 1 warning in 184.76s (0:03:04)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.23.0-self-spec-source` -> `Total findings: 0`

## Release-surface results

- Branch push proof: the tested release candidate was pushed to origin at `d6aceff` before later chronology-only reconciliation.
- Annotated tag: `v1.23.0` object `b592b7d` peels to tested release commit `d6aceff`.
- Publish attempt: `uv publish --keyring-provider subprocess <built artifacts>` failed with `Missing credentials for https://upload.pypi.org/legacy/`.
- PyPI verification after the failed publish: project JSON still reports `info.version = 1.22.0`, `releases["1.23.0"]` is absent, and the project page does not show `1.23.0` live.

## Current truth

- `agentkit-cli v1.23.0` is **not shipped**.
- The last shipped line remains `v1.22.0`.
- The tested release candidate commit is still `d6aceff`, and the pushed tag points there.
- Any later branch head on `feat/v1.23.0-self-spec-source` is chronology-only and must not be confused with shipped registry truth.
