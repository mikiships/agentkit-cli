# BUILD-REPORT.md — agentkit-cli v1.23.0 release completion

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.23.0-release.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Re-ran release truth sweep from `d6aceff` and confirmed no contradictory success or blocker narratives. |
| D2 | ✅ Complete | Re-ran the focused self-spec slice, full suite, and hygiene checks from the current tree. |
| D3 | ✅ Complete | Branch push and annotated tag succeeded, and PyPI went live once the release used the working `.pypirc` auth path via `uvx twine upload` from the tagged release tree. |
| D4 | ✅ Complete | Repo and workspace chronology surfaces now distinguish the shipped tag truth from later docs-only chronology commits. |

## Validation

- `python3 -m agentkit_cli.main source-audit . --json` -> `ready_for_contract: true`, `blocker_count: 0`, `used_fallback: false`
- `python3 -m agentkit_cli.main spec . --output-dir <temp-dir> --json` -> succeeded and wrote deterministic artifacts
- `python3 -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py tests/test_daily_d5.py` -> `34 passed in 1.47s`
- `uv run python -m pytest -q` -> `5003 passed, 1 warning in 184.76s (0:03:04)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.23.0-self-spec-source` -> `Total findings: 0`

## Release-surface results

- Branch push proof: the tested release candidate was pushed to origin at `d6aceff` before later chronology-only reconciliation.
- Annotated tag: `v1.23.0` object `b592b7d` peels to tested release commit `d6aceff`.
- Publish proof: the tagged release commit was built from a detached temp worktree, then uploaded with `uvx twine upload --skip-existing` using the existing `.pypirc` auth path.
- PyPI verification after publish: both `https://pypi.org/pypi/agentkit-cli/1.23.0/json` and `https://pypi.org/pypi/agentkit-cli/json` report `info.version = 1.23.0`, and the live files are the wheel plus sdist for `1.23.0`.

## Current truth

- `agentkit-cli v1.23.0` is **shipped**.
- The last shipped line is now `v1.23.0`.
- The tested release candidate commit is still `d6aceff`, and the pushed tag points there.
- Any later branch head on `feat/v1.23.0-self-spec-source` is chronology-only and must not be confused with shipped registry truth.
