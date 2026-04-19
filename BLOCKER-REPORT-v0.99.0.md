# BLOCKER REPORT — agentkit-cli v0.99.0 release

Date: 2026-04-19
Branch: rc/v0.99.0-mainline

## Blocker

PyPI publish is blocked by missing credentials in this environment.

## Completed before block

- D1 verification baseline complete
- D2 branch/tag push complete
- release branch pushed: `origin/rc/v0.99.0-mainline` -> `3b2f21df8defa08cbdcfe5b69c140d02292ecdf6`
- release tag pushed: `v0.99.0` -> annotated tag object `7b6bca32d571bc411596403681b02bfc3c5d3fe2`, dereferenced commit `3b2f21df8defa08cbdcfe5b69c140d02292ecdf6`
- targeted validation: `84 passed in 1.37s`
- full suite: `4775 passed, 1 warning in 126.39s (0:02:06)`
- build artifacts created successfully:
  - `dist/agentkit_cli-0.99.0.tar.gz`
  - `dist/agentkit_cli-0.99.0-py3-none-any.whl`

## Failed attempts on the same issue

1. `uv publish --dry-run dist/*`
   - result: trusted publishing unavailable, no OIDC token discovered, and no credentials configured
2. `uv publish --keyring-provider subprocess dist/*`
   - result: upload failed with `Missing credentials for https://upload.pypi.org/legacy/`
3. `security find-internet-password -s upload.pypi.org -g`
   - result: `The specified item could not be found in the keychain.`

## Truthful release state at stop

- tests: green locally from this repo
- branch: pushed
- tag: pushed
- artifacts: built locally
- registry: NOT live, publish blocked
- release status: NOT SHIPPED

## What is needed next

Provide valid PyPI credentials for `agentkit-cli` in a supported path for this machine, then rerun D3 publish and registry verification before any shipped claim.
