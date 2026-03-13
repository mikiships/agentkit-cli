# BUILD-REPORT: agentkit-cli v0.6.0

## What Was Built

### `agentkit publish` (D1)
New subcommand at `agentkit_cli/publish.py`. Implements the here.now 3-step publish flow:
1. POST `/v1/publish` to get upload URLs + finalize URL
2. PUT HTML file content to upload URL
3. POST finalize URL to get public URL

Features:
- `HERENOW_API_KEY` env var for authenticated (persistent) publishes
- Anonymous fallback with 24h expiry notice
- `--json` flag: outputs `{"url": "...", "expires_in": "24h"}`
- `--quiet` flag: only prints the URL
- Clear error messages (file not found → hint to run `agentkit report`)
- Registered as `agentkit publish [HTML_PATH]` in `main.py`

### `--publish` flags (D2)
- `agentkit run --publish`: publishes HTML report after pipeline finishes; failure is non-fatal
- `agentkit report --publish`: publishes HTML report after generation; failure is non-fatal

### Tests (D3)
10 new tests in `tests/test_publish.py`, all passing, all using mocks (no real HTTP calls):
- Anonymous and authenticated success paths
- FileNotFoundError with helpful message
- Step 1/2/3 HTTP failures (503, 403, 500)
- `--json` output validation
- `--quiet` output validation
- `run --publish` flag integration (publish called, non-fatal)
- `report --publish` flag integration (publish called, non-fatal on failure)

### Docs + version bump (D4)
- `README.md`: "Sharing Results" section added after `agentkit report` section
- `CHANGELOG.md`: `## v0.6.0` entry added
- `pyproject.toml`: version `0.5.1` → `0.6.0`
- `agentkit_cli/__init__.py`: version `0.5.0` → `0.6.0`

## Test Count

**220 tests passing** (210 existing + 10 new). No regressions.

## Git Log

```
55161d5 D4: add Sharing Results docs, CHANGELOG v0.6.0, bump version to 0.6.0
17676fa D3: add 10 tests for publish command (220 total passing)
fb1fb2d D2: add --publish flag to run and report commands
494102b D1: add agentkit publish command (here.now 3-step API)
```

## Deviations from Contract

None. All checklist items satisfied:
- `publish.py` with 3-step here.now API ✓
- Auth via `HERENOW_API_KEY` ✓
- Anonymous fallback with 24h notice ✓
- File-not-found error with hint ✓
- Registered in `cli.py` (main.py) ✓
- `agentkit run --publish` ✓
- `agentkit report --publish` ✓
- Publish failure non-fatal in both ✓
- 10 new tests, all mocked ✓
- README "Sharing Results" section ✓
- CHANGELOG v0.6.0 entry ✓
- Version bumped to 0.6.0 ✓
- `agentkit --version` returns 0.6.0 ✓
- No PyPI publish ✓
- No real HTTP calls in tests ✓
