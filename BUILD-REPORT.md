# BUILD-REPORT.md — agentkit-cli v1.24.0 release completion

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.24.0-release.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Re-grounded the dirty partial-release tree, removed stale `.release-check/` temp evidence, and landed the truthful tested release candidate at `6790e96`. |
| D2 | ✅ Complete | Re-ran the focused JSON-stdout slice, direct stdout/stderr proof, full suite, and hygiene checks from the current tree. |
| D3 | ✅ Complete | Branch push, annotated tag, PyPI publish, and post-publish verification all succeeded for `v1.24.0`. |
| D4 | ✅ Complete | Repo and workspace chronology surfaces distinguish the shipped tag truth from the later docs-only branch head. |

## Validation

- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py` -> `8 passed in 0.94s`
- Direct command-path proof:
  - `uv run python -m agentkit_cli.main spec . --output-dir "$tmpdir/specdir" --json > "$tmpdir/spec.json" 2> "$tmpdir/spec.stderr"`
  - `python3 - <<'PY' "$tmpdir/spec.json" "$tmpdir/spec.stderr" ... json.loads(...) ... PY` -> `parsed schema_version=agentkit.spec.v1 primary_kind=None`
  - stderr contained `Wrote spec directory: ...`
- `uv run python -m pytest -q` -> `5004 passed, 1 warning in 196.61s (0:03:16)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.24.0-json-clean-stdout` -> `Total findings: 0`

## Release-surface results

- Branch push proof: the tested release candidate was pushed to origin at `6790e96` before later chronology-only reconciliation.
- Annotated tag: `v1.24.0` object `1f86c6593ba308bf004ac67cacb3e35ddaa9ebbe` peels to tested release commit `6790e964cfb654fef87e7cbae55695aeb3e268ea`.
- Publish proof: built exact `1.24.0` artifacts with `uv build`, then uploaded `dist/agentkit_cli-1.24.0.tar.gz` and `dist/agentkit_cli-1.24.0-py3-none-any.whl` using `uvx twine upload --skip-existing`.
- PyPI verification after publish: both `https://pypi.org/pypi/agentkit-cli/json` and `https://pypi.org/pypi/agentkit-cli/1.24.0/json` report `info.version = 1.24.0`, and the live files are the wheel plus sdist for `1.24.0`. The exact project page URL `https://pypi.org/project/agentkit-cli/1.24.0/` returns `200`, though non-browser fetches still see PyPI's client-challenge HTML.

## Current truth

- `agentkit-cli v1.24.0` is **shipped**.
- The last shipped line is now `v1.24.0`.
- The tested release candidate commit is still `6790e96`, and the pushed tag points there.
- Any later branch head on `feat/v1.24.0-json-clean-stdout` is chronology-only and must not be confused with shipped registry truth.
