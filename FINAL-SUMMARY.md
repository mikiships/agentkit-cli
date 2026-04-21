# Final Summary — agentkit-cli v1.22.0 release completion

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.22.0-release.md

## Outcome

SHIPPED

- `agentkit-cli v1.22.0` is live.
- `agentkit spec` is now shipped as the deterministic planning step between `map` and `contract`, with direct contract seeding through `agentkit contract --spec`.
- The shipped tag is `v1.22.0` -> `2c2b89f`, while `origin/feat/v1.22.0-spec` later advanced to docs-only chronology head `4257eee`.
- Active repo and workspace chronology surfaces were reconciled to that exact split.

## Four surfaces proven

- Tests: focused release slice passed at `37 passed in 2.31s`, and full suite passed at `5003 passed, 1 warning in 187.11s (0:03:07)`.
- Branch/tag: `origin/feat/v1.22.0-spec` exists at `4257eee`; annotated tag `v1.22.0` exists on origin and peels to shipped release commit `2c2b89f`.
- PyPI publish: build produced both `agentkit_cli-1.22.0-py3-none-any.whl` and `agentkit_cli-1.22.0.tar.gz`, and publish succeeded via `uvx twine upload` after the base interpreter lacked `twine`.
- Registry verification: PyPI version JSON for `agentkit-cli/1.22.0` returns `200` and lists both wheel (`704554` bytes) and sdist (`1231351` bytes); the project page URL for `1.22.0` was also returned by the successful publish flow.
