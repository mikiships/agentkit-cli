# BUILD-REPORT.md — agentkit-cli v1.17.0 resume lanes

Status: SHIPPED
Date: 2026-04-20
Contract: all-day-build-contract-agentkit-cli-v1.17.0-release.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Recalled release context, ran the status-conflict scan, confirmed `1.17.0` version surfaces, and recorded the exact pre-release truth from this repo |
| D2 | ✅ Complete | Re-ran the focused resume plus adjacent reconcile slice and the full suite from this repo, both passing |
| D3 | ✅ Complete | Pushed `feat/v1.17.0-resume-lanes`, created annotated tag `v1.17.0`, pushed the tag, and verified both remote refs explicitly |
| D4 | ✅ Complete | Built `agentkit_cli-1.17.0.tar.gz` and `agentkit_cli-1.17.0-py3-none-any.whl`, published them to PyPI, and verified live registry JSON |
| D5 | ✅ Complete | Reconciled the shipped narrative so the repo now distinguishes the shipped release commit from the later docs-only chronology head |

## Validation

- Focused release slice: `uv run python -m pytest -q tests/test_resume_engine.py tests/test_reconcile_engine.py tests/test_resume_cmd.py tests/test_resume_workflow.py tests/test_main.py` -> `21 passed in 6.46s`
- Full suite: `uv run python -m pytest -q tests/` -> `4959 passed, 1 warning in 338.18s (0:05:38)`
- Remote branch verification: `git ls-remote --heads origin feat/v1.17.0-resume-lanes` -> `533354a9e9074c9bf26923c28f7eedce0a8c8339`
- Remote tag verification: `git ls-remote --tags origin v1.17.0^{}` -> `533354a9e9074c9bf26923c28f7eedce0a8c8339`
- Registry verification: `https://pypi.org/pypi/agentkit-cli/1.17.0/json` -> live with `agentkit_cli-1.17.0.tar.gz` and `agentkit_cli-1.17.0-py3-none-any.whl`

## Repo state

- Branch: `feat/v1.17.0-resume-lanes`
- Shipped release commit: `533354a9e9074c9bf26923c28f7eedce0a8c8339` (`chore: refresh v1.17.0 release verification`)
- Supported handoff lane: `source -> source-audit -> map -> contract -> bundle -> taskpack -> clarify -> resolve -> dispatch -> stage -> materialize -> launch -> observe -> supervise -> reconcile -> resume`
- Version surfaces target `1.17.0` in `pyproject.toml`, `agentkit_cli/__init__.py`, and `uv.lock`
- Branch chronology may advance beyond the shipped tag only for docs-only release narration cleanup
- Working tree is clean except for the intentional untracked release-contract artifacts
