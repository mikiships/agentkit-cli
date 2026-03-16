"""Tool detection and subprocess execution utilities.

Contains the ``ToolAdapter`` — the single source of truth for all quartet tool
invocations (agentmd, agentlint, coderace, agentreflect).  Every command that
calls these tools MUST use ToolAdapter methods.  Never hand-roll subprocess
calls to quartet tools outside this module.
"""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


QUARTET_TOOLS = ["agentmd", "coderace", "agentlint", "agentreflect"]

INSTALL_HINTS = {
    "agentmd": "pip install agentmd",
    "coderace": "pip install coderace",
    "agentlint": "pip install agentlint",
    "agentreflect": "pip install agentreflect",
}


def which(tool: str) -> Optional[str]:
    """Return path to tool if installed, else None."""
    return shutil.which(tool)


def is_installed(tool: str) -> bool:
    return which(tool) is not None


def get_version(tool: str) -> Optional[str]:
    """Try to get the version string for a tool."""
    path = which(tool)
    if not path:
        return None
    for flag in ["--version", "version"]:
        try:
            result = subprocess.run(
                [path, flag],
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = (result.stdout + result.stderr).strip()
            if output:
                # Return first line
                return output.splitlines()[0]
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue
    return "installed"


def run_tool(tool: str, args: list[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    """Run a quartet tool via subprocess."""
    path = which(tool)
    if not path:
        raise FileNotFoundError(f"Tool not found: {tool}. Install with: {INSTALL_HINTS.get(tool, f'pip install {tool}')}")
    return subprocess.run(
        [path] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def tool_status() -> dict[str, dict]:
    """Return status dict for all quartet tools."""
    result = {}
    for tool in QUARTET_TOOLS:
        installed = is_installed(tool)
        result[tool] = {
            "installed": installed,
            "path": which(tool) if installed else None,
            "version": get_version(tool) if installed else None,
        }
    return result


# ---------------------------------------------------------------------------
# ToolAdapter — canonical quartet invocations
# ---------------------------------------------------------------------------

_TOOL_TIMEOUT = 60
_REFLECT_TIMEOUT = 30


def _parse_json_output(raw: str) -> Optional[dict]:
    """Extract JSON from tool stdout, tolerating non-JSON prefix lines."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    for ch in ('{', '['):
        idx = raw.find(ch)
        if idx != -1:
            try:
                return json.loads(raw[idx:])
            except json.JSONDecodeError:
                pass
    return None


class ToolAdapter:
    """Single source of truth for all quartet tool invocations.

    Every command that calls agentmd/agentlint/coderace/agentreflect
    MUST use these methods.  Never hand-roll subprocess calls to these tools.
    """

    def __init__(self, timeout: int = _TOOL_TIMEOUT) -> None:
        self.timeout = timeout

    # -- internal helpers ---------------------------------------------------

    def _run(self, cmd: list[str], cwd: Optional[str] = None,
             timeout: Optional[int] = None,
             stdin_data: Optional[str] = None) -> Optional[subprocess.CompletedProcess]:
        """Run a subprocess, returning None on any failure."""
        t = timeout or self.timeout
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=t,
                cwd=cwd,
                input=stdin_data,
            )
            if result.returncode != 0:
                logger.warning("Tool %s returned exit %d: %s",
                               cmd[0], result.returncode, result.stderr[:200])
                return None
            return result
        except FileNotFoundError:
            logger.warning("Tool %s not found on PATH", cmd[0])
            return None
        except subprocess.TimeoutExpired:
            logger.warning("Tool %s timed out after %ds", cmd[0], t)
            return None
        except Exception as exc:
            logger.warning("Tool %s error: %s", cmd[0], exc)
            return None

    def _run_json(self, cmd: list[str], cwd: Optional[str] = None,
                  timeout: Optional[int] = None,
                  stdin_data: Optional[str] = None) -> Optional[dict]:
        """Run a subprocess and parse JSON from its stdout."""
        result = self._run(cmd, cwd=cwd, timeout=timeout, stdin_data=stdin_data)
        if result is None:
            return None
        data = _parse_json_output(result.stdout)
        if data is None:
            logger.warning("Could not parse JSON from %s output", cmd[0])
        return data

    def _tool_path(self, tool: str) -> Optional[str]:
        return which(tool)

    # -- agentlint ----------------------------------------------------------

    def agentlint_check_context(self, path: str) -> Optional[dict]:
        """Run ``agentlint check-context . --format json``."""
        if not is_installed("agentlint"):
            return None
        return self._run_json(
            ["agentlint", "check-context", ".", "--format", "json"],
            cwd=path,
        )

    def agentlint_diff(self, diff_content: str, path: str) -> Optional[dict]:
        """Run ``agentlint check --format json`` with diff on stdin."""
        if not is_installed("agentlint"):
            return None
        return self._run_json(
            ["agentlint", "check", "--format", "json"],
            cwd=path,
            stdin_data=diff_content,
        )

    # -- agentmd ------------------------------------------------------------

    def agentmd_score(self, path: str) -> Optional[dict]:
        """Run ``agentmd score . --json`` with fallback to ``agentmd generate --json``."""
        if not is_installed("agentmd"):
            return None
        result = self._run_json(["agentmd", "score", ".", "--json"], cwd=path)
        if result is not None:
            return result
        return self._run_json(["agentmd", "generate", "--json"], cwd=path)

    def agentmd_generate(self, path: str, minimal: bool = False) -> Optional[dict]:
        """Run ``agentmd generate [--minimal] --json``."""
        if not is_installed("agentmd"):
            return None
        cmd = ["agentmd", "generate"]
        if minimal:
            cmd.append("--minimal")
        cmd.append("--json")
        return self._run_json(cmd, cwd=path)

    # -- coderace -----------------------------------------------------------

    def coderace_benchmark_history(self, path: str) -> Optional[dict]:
        """Run ``coderace benchmark history --format json``."""
        if not is_installed("coderace"):
            return None
        result = self._run_json(
            ["coderace", "benchmark", "history", "--format", "json"],
            cwd=path,
        )
        if result is None:
            return {"status": "no_results",
                    "message": "Run coderace benchmark to populate data"}
        return result

    # -- agentreflect -------------------------------------------------------

    def agentreflect_from_git(self, path: str) -> Optional[dict]:
        """Run ``agentreflect generate --from-git --format markdown``.

        Returns ``{"suggestions_md": text, "count": N}`` or None.
        """
        if not is_installed("agentreflect"):
            return None
        result = self._run(
            ["agentreflect", "generate", "--from-git", "--format", "markdown"],
            cwd=path,
            timeout=_REFLECT_TIMEOUT,
        )
        if result is None:
            return None
        text = result.stdout.strip()
        return {"suggestions_md": text, "count": text.count("###")}

    def agentreflect_from_notes(self, path: str, notes_file: str) -> Optional[dict]:
        """Run ``agentreflect generate --from-notes <file> --format markdown``.

        Returns ``{"suggestions_md": text, "count": N}`` or None.
        """
        if not is_installed("agentreflect"):
            return None
        result = self._run(
            ["agentreflect", "generate", "--from-notes", notes_file,
             "--format", "markdown"],
            cwd=path,
            timeout=_REFLECT_TIMEOUT,
        )
        if result is None:
            return None
        text = result.stdout.strip()
        return {"suggestions_md": text, "count": text.count("###")}


# Module-level singleton for convenience imports
_default_adapter: Optional[ToolAdapter] = None


def get_adapter() -> ToolAdapter:
    """Return the module-level ToolAdapter singleton."""
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = ToolAdapter()
    return _default_adapter
