"""Tool runner utilities for agentkit report command."""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

TOOL_TIMEOUT = 60  # seconds default
REFLECT_TIMEOUT = 30


def _is_installed(tool: str) -> bool:
    return shutil.which(tool) is not None


def _run(cmd: list[str], cwd: str, timeout: int) -> Optional[subprocess.CompletedProcess]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        if result.returncode != 0:
            logger.warning("Tool %s returned non-zero exit %d: %s", cmd[0], result.returncode, result.stderr[:200])
            return None
        return result
    except FileNotFoundError:
        logger.warning("Tool %s not found on PATH", cmd[0])
        return None
    except subprocess.TimeoutExpired:
        logger.warning("Tool %s timed out after %ds", cmd[0], timeout)
        return None
    except Exception as exc:
        logger.warning("Tool %s error: %s", cmd[0], exc)
        return None


def _parse_json_output(raw: str) -> Optional[dict]:
    """Try to extract JSON from stdout. Some tools prefix with non-JSON lines."""
    # Try full string first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Try finding first '{' or '['
    for ch in ('{', '['):
        idx = raw.find(ch)
        if idx != -1:
            try:
                return json.loads(raw[idx:])
            except json.JSONDecodeError:
                pass
    return None


def run_agentlint_check(path: str) -> Optional[dict]:
    """Run agentlint check-context on path, return parsed JSON or None."""
    if not _is_installed("agentlint"):
        return None
    # Fix D1: correct flag is --format json, not --json
    result = _run(["agentlint", "check-context", ".", "--format", "json"], cwd=path, timeout=TOOL_TIMEOUT)
    if result is None:
        return None
    data = _parse_json_output(result.stdout)
    if data is None:
        logger.warning("agentlint: could not parse JSON output")
        return None
    return data


def run_agentmd_score(path: str) -> Optional[dict]:
    """Run agentmd score on path, return parsed JSON or None."""
    if not _is_installed("agentmd"):
        return None
    # Try 'agentmd score . --json' first; fall back to 'agentmd generate --json'
    result = _run(["agentmd", "score", ".", "--json"], cwd=path, timeout=TOOL_TIMEOUT)
    if result is None:
        result = _run(["agentmd", "generate", "--json"], cwd=path, timeout=TOOL_TIMEOUT)
    if result is None:
        return None
    data = _parse_json_output(result.stdout)
    if data is None:
        logger.warning("agentmd: could not parse JSON output")
        return None
    return data


def run_coderace_bench(path: str) -> Optional[dict]:
    """Check coderace benchmark history for cached results.

    Fix D2: coderace has no --json flag on benchmark. Instead check history
    for cached results. Returns a graceful no_results dict if none found.
    """
    if not _is_installed("coderace"):
        return None
    # Try to fetch cached benchmark history (no live agents required)
    result = _run(["coderace", "benchmark", "history"], cwd=path, timeout=TOOL_TIMEOUT)
    if result is None:
        # coderace is installed but history command failed or no results
        return {"status": "no_results", "message": "Run coderace benchmark to populate data"}
    # Try to parse JSON from history output
    data = _parse_json_output(result.stdout)
    if data is None:
        # History output exists but isn't parseable JSON — treat as no cached data
        logger.warning("coderace: benchmark history output not parseable as JSON")
        return {"status": "no_results", "message": "Run coderace benchmark to populate data"}
    return data


def run_agentreflect_analyze(path: str) -> Optional[dict]:
    """Run agentreflect generate on path, return dict with markdown suggestions.

    Fix D3: --format json is not supported. Use --from-git --format markdown
    and return the text as {"suggestions_md": text, "count": N}.
    """
    if not _is_installed("agentreflect"):
        return None
    result = _run(
        ["agentreflect", "generate", "--from-git", "--format", "markdown"],
        cwd=path,
        timeout=REFLECT_TIMEOUT,
    )
    if result is None:
        return None
    text = result.stdout.strip()
    return {
        "suggestions_md": text,
        "count": text.count("###"),
    }
