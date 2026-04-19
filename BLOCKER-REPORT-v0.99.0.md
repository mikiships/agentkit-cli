# RESOLUTION NOTE — agentkit-cli v0.99.0 release blocker superseded

Date: 2026-04-19
Branch: rc/v0.99.0-mainline

## Resolution

This file records the earlier blocker state, but it is no longer the current release truth.

A later verification pass confirmed that `agentkit-cli==0.99.0` is live on PyPI, so the release is now shipped.

## Earlier blocker context

The prior pass stopped after three credential-path attempts and correctly refused to claim shipment without registry proof.

## Superseding source of truth

- `BUILD-REPORT-v0.99.0.md`
- `BUILD-REPORT.md`
- `progress-log.md`

## Final verified release state

- targeted validation: `84 passed in 1.36s`
- full suite: `4775 passed, 1 warning in 127.61s (0:02:07)`
- release branch on origin: `rc/v0.99.0-mainline` -> `d9cb8cf763c97b7ecc8794f827853cc3d57738f0`
- shipped release tag: `v0.99.0` -> `3b2f21df8defa08cbdcfe5b69c140d02292ecdf6`
- PyPI live proof:
  - `agentkit_cli-0.99.0-py3-none-any.whl` uploaded `2026-04-19T02:24:46.882825Z`
  - `agentkit_cli-0.99.0.tar.gz` uploaded `2026-04-19T02:24:48.497683Z`
- release status: SHIPPED
