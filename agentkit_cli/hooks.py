"""HookEngine: install/uninstall/status/check git and pre-commit hooks."""
from __future__ import annotations

import os
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

# ---------------------------------------------------------------------------
# Git hook script template
# ---------------------------------------------------------------------------

_GIT_HOOK_HEADER = "# agentkit quality gate (installed by agentkit hooks)"

_GIT_HOOK_TEMPLATE = """\
#!/bin/sh
{header}
# min-score: {min_score}
agentkit score --quiet --min-score {min_score} || exit 1
"""

# ---------------------------------------------------------------------------
# pre-commit config entry
# ---------------------------------------------------------------------------

_PRECOMMIT_REPO_URL = "https://github.com/mikiships/agentkit-cli"
_PRECOMMIT_HOOK_ID = "agentkit-score"


def _precommit_entry(min_score: int) -> dict[str, Any]:
    return {
        "repo": _PRECOMMIT_REPO_URL,
        "rev": "main",
        "hooks": [
            {
                "id": _PRECOMMIT_HOOK_ID,
                "args": [f"--min-score={min_score}"],
            }
        ],
    }


# ---------------------------------------------------------------------------
# HookEngine
# ---------------------------------------------------------------------------


class HookEngine:
    """Manage agentkit pre-commit quality gate hooks."""

    def install(
        self,
        path: Path,
        mode: str = "both",
        min_score: int = 60,
        fail_on_drop: bool = False,
    ) -> dict[str, Any]:
        """Install hooks at *path*.

        *mode* is ``"git"``, ``"precommit"``, or ``"both"`` (default).
        Returns a dict describing what was installed.
        """
        path = Path(path).resolve()
        results: dict[str, Any] = {"git": None, "precommit": None}

        if mode in ("git", "both"):
            results["git"] = self._install_git_hook(path, min_score)

        if mode in ("precommit", "both"):
            results["precommit"] = self._install_precommit_hook(path, min_score)

        return results

    def uninstall(self, path: Path, mode: str = "both") -> dict[str, Any]:
        """Remove agentkit hooks at *path*."""
        path = Path(path).resolve()
        results: dict[str, Any] = {"git": None, "precommit": None}

        if mode in ("git", "both"):
            results["git"] = self._uninstall_git_hook(path)

        if mode in ("precommit", "both"):
            results["precommit"] = self._uninstall_precommit_hook(path)

        return results

    def status(self, path: Path) -> dict[str, Any]:
        """Return hook installation status for *path*."""
        path = Path(path).resolve()
        git_hook = path / ".git" / "hooks" / "pre-commit"
        precommit_cfg = path / ".pre-commit-config.yaml"

        git_installed = False
        git_min_score: int | None = None
        if git_hook.exists():
            content = git_hook.read_text(encoding="utf-8")
            git_installed = _GIT_HOOK_HEADER in content
            if git_installed:
                for line in content.splitlines():
                    if line.startswith("# min-score:"):
                        try:
                            git_min_score = int(line.split(":")[1].strip())
                        except (ValueError, IndexError):
                            pass

        precommit_installed = False
        if precommit_cfg.exists():
            try:
                data = yaml.safe_load(precommit_cfg.read_text(encoding="utf-8")) or {}
                for repo in data.get("repos", []):
                    if repo.get("repo") == _PRECOMMIT_REPO_URL:
                        for hook in repo.get("hooks", []):
                            if hook.get("id") == _PRECOMMIT_HOOK_ID:
                                precommit_installed = True
            except Exception:  # noqa: BLE001
                pass

        return {
            "git_installed": git_installed,
            "precommit_installed": precommit_installed,
            "min_score": git_min_score,
            "last_check": None,
        }

    def check(self, path: Path) -> dict[str, Any]:
        """Run agentkit score directly (same as what the hook would run)."""
        path = Path(path).resolve()
        st = self.status(path)
        min_score = st.get("min_score") or 60

        result = subprocess.run(
            [sys.executable, "-m", "agentkit_cli.main", "score", "--quiet", "--min-score", str(min_score)],
            cwd=str(path),
            capture_output=True,
            text=True,
        )
        passed = result.returncode == 0
        return {
            "passed": passed,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "min_score": min_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _install_git_hook(self, path: Path, min_score: int) -> dict[str, str]:
        git_dir = path / ".git"
        if not git_dir.is_dir():
            return {"status": "skipped", "reason": "not a git repository"}

        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_path = hooks_dir / "pre-commit"

        # idempotent: overwrite if already ours, otherwise don't clobber
        if hook_path.exists():
            existing = hook_path.read_text(encoding="utf-8")
            if _GIT_HOOK_HEADER not in existing:
                return {
                    "status": "skipped",
                    "reason": "pre-commit hook exists but was not installed by agentkit",
                }

        script = _GIT_HOOK_TEMPLATE.format(header=_GIT_HOOK_HEADER, min_score=min_score)
        hook_path.write_text(script, encoding="utf-8")
        # make executable
        current_mode = hook_path.stat().st_mode
        hook_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        return {"status": "installed", "path": str(hook_path)}

    def _install_precommit_hook(self, path: Path, min_score: int) -> dict[str, str]:
        cfg_path = path / ".pre-commit-config.yaml"
        entry = _precommit_entry(min_score)

        if cfg_path.exists():
            try:
                data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            except Exception:  # noqa: BLE001
                data = {}
        else:
            data = {}

        repos: list[dict[str, Any]] = data.get("repos", []) or []

        # find existing agentkit entry and update, or append
        updated = False
        for repo in repos:
            if repo.get("repo") == _PRECOMMIT_REPO_URL:
                repo["hooks"] = entry["hooks"]
                repo["rev"] = entry["rev"]
                updated = True
                break

        if not updated:
            repos.append(entry)

        data["repos"] = repos
        cfg_path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")

        return {"status": "installed", "path": str(cfg_path)}

    def _uninstall_git_hook(self, path: Path) -> dict[str, str]:
        hook_path = path / ".git" / "hooks" / "pre-commit"
        if not hook_path.exists():
            return {"status": "not_found"}

        content = hook_path.read_text(encoding="utf-8")
        if _GIT_HOOK_HEADER not in content:
            return {"status": "skipped", "reason": "hook not installed by agentkit"}

        hook_path.unlink()
        return {"status": "removed", "path": str(hook_path)}

    def _uninstall_precommit_hook(self, path: Path) -> dict[str, str]:
        cfg_path = path / ".pre-commit-config.yaml"
        if not cfg_path.exists():
            return {"status": "not_found"}

        try:
            data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            return {"status": "error", "reason": "could not parse YAML"}

        repos: list[dict[str, Any]] = data.get("repos", []) or []
        new_repos = [r for r in repos if r.get("repo") != _PRECOMMIT_REPO_URL]
        if len(new_repos) == len(repos):
            return {"status": "not_found"}

        data["repos"] = new_repos
        cfg_path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
        return {"status": "removed", "path": str(cfg_path)}
