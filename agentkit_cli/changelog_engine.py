"""agentkit changelog engine — git log + quality score delta → markdown changelog."""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CommitSummary:
    hash: str
    message: str
    files_changed: int
    author: str
    ts: str


@dataclass
class ScoreDelta:
    before: float
    after: float
    delta: float
    project: str


# ---------------------------------------------------------------------------
# Conventional-commit prefix grouping
# ---------------------------------------------------------------------------

_CC_PREFIXES = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "docs": "Documentation",
    "refactor": "Refactoring",
    "test": "Tests",
    "chore": "Chores",
    "ci": "CI",
    "perf": "Performance",
    "style": "Style",
    "build": "Build",
}

_CC_RE = re.compile(r"^(\w+)(?:\([^)]*\))?\!?:\s*(.+)$")


def _detect_prefix(message: str) -> str:
    m = _CC_RE.match(message.strip())
    if m:
        prefix = m.group(1).lower()
        return prefix if prefix in _CC_PREFIXES else "other"
    return "other"


def _clean_message(message: str) -> str:
    m = _CC_RE.match(message.strip())
    if m:
        return m.group(2)
    return message.strip()


# ---------------------------------------------------------------------------
# ChangelogEngine
# ---------------------------------------------------------------------------

class ChangelogEngine:
    """Parse git log and quality score history to produce changelog content."""

    # ---- data sources ----

    @staticmethod
    def from_git(since: Optional[str], path: str = ".") -> list[CommitSummary]:
        """Parse git log since a ref (or last tag if since is None).

        Falls back to HEAD~10 if no tags exist. Returns empty list if git
        is not available or there are no commits.
        """
        try:
            # Determine base ref
            if since is None:
                since = ChangelogEngine._last_tag(path)

            if since:
                log_range = f"{since}..HEAD"
            else:
                log_range = "HEAD~10..HEAD"

            sep = "|||COMMIT|||"
            fmt = f"{sep}%H%n%s%n%aN%n%cI"
            result = subprocess.run(
                ["git", "log", f"--format={fmt}", "--numstat", log_range],
                capture_output=True,
                text=True,
                cwd=path,
                timeout=30,
            )
            if result.returncode != 0:
                return []

            return ChangelogEngine._parse_git_output(result.stdout, sep)
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            return []

    @staticmethod
    def _last_tag(path: str = ".") -> Optional[str]:
        """Return the most recent git tag reachable from HEAD, or None."""
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                cwd=path,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    @staticmethod
    def _parse_git_output(raw: str, sep: str) -> list[CommitSummary]:
        """Parse the combined --format + --numstat git log output."""
        commits: list[CommitSummary] = []
        blocks = raw.split(sep)
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            lines = block.splitlines()
            if len(lines) < 4:
                continue
            hash_ = lines[0].strip()
            message = lines[1].strip()
            author = lines[2].strip()
            ts = lines[3].strip()
            # Count files from numstat lines (added\tdeleted\tfile)
            files_changed = 0
            for line in lines[4:]:
                parts = line.split("\t")
                if len(parts) == 3 and (parts[0].isdigit() or parts[1].isdigit()):
                    files_changed += 1
            if hash_ and message:
                commits.append(CommitSummary(
                    hash=hash_,
                    message=message,
                    files_changed=files_changed,
                    author=author,
                    ts=ts,
                ))
        return commits

    @staticmethod
    def from_history(
        project: Optional[str],
        since_days: int = 7,
        db_path: Optional[str] = None,
    ) -> Optional[ScoreDelta]:
        """Read agentkit history DB, find score delta over the last N days.

        Returns None if DB missing, no runs found, or only one data point.
        """
        try:
            from agentkit_cli.history import HistoryDB
            from pathlib import Path as _Path

            db = HistoryDB(_Path(db_path)) if db_path else HistoryDB()
            proj = project or _Path(".").resolve().name
            rows = db.get_history(project=proj, tool="overall", limit=100)
            if not rows:
                return None

            cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
            older = [r for r in rows if _parse_ts(r["ts"]) < cutoff]
            newer = [r for r in rows if _parse_ts(r["ts"]) >= cutoff]

            if not newer:
                return None

            after = newer[0]["score"]  # most recent
            if older:
                before = older[0]["score"]  # most recent before cutoff
            elif len(newer) > 1:
                before = newer[-1]["score"]  # oldest in newer window
            else:
                return None

            return ScoreDelta(
                before=round(before, 1),
                after=round(after, 1),
                delta=round(after - before, 1),
                project=proj,
            )
        except Exception:
            return None

    # ---- renderers ----

    @staticmethod
    def render_markdown(
        commits: list[CommitSummary],
        score_delta: Optional[ScoreDelta],
        version: Optional[str] = None,
    ) -> str:
        """Render a clean markdown changelog section."""
        lines: list[str] = []

        header = f"## {version}" if version else "## Unreleased"
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        lines.append(f"{header} — {today}")
        lines.append("")

        if score_delta is not None:
            sign = "+" if score_delta.delta >= 0 else ""
            lines.append(f"**Quality score:** {score_delta.before} → {score_delta.after} ({sign}{score_delta.delta})")
            lines.append("")

        if not commits:
            lines.append("_No changes since last tag._")
            return "\n".join(lines)

        groups: dict[str, list[str]] = {}
        for commit in commits:
            prefix = _detect_prefix(commit.message)
            group_name = _CC_PREFIXES.get(prefix, "Changes")
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(_clean_message(commit.message))

        # Preferred order
        order = ["Features", "Bug Fixes", "Performance", "Documentation",
                 "Refactoring", "Tests", "CI", "Build", "Style", "Chores", "Changes"]
        for group in order:
            if group not in groups:
                continue
            lines.append(f"### {group}")
            lines.append("")
            for msg in groups[group]:
                lines.append(f"- {msg}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def render_release(
        commits: list[CommitSummary],
        score_delta: Optional[ScoreDelta],
        version: Optional[str] = None,
        no_chore: bool = True,
    ) -> str:
        """Render a GitHub release body (strips chore/test/ci by default, adds pip install)."""
        _EXCLUDE = {"chore", "test", "ci", "build", "style"}

        filtered = [c for c in commits if _detect_prefix(c.message) not in _EXCLUDE] if no_chore else commits

        lines: list[str] = []
        header = f"## {version}" if version else "## Release"
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        lines.append(f"{header} — {today}")
        lines.append("")

        if score_delta is not None:
            sign = "+" if score_delta.delta >= 0 else ""
            lines.append(f"**Quality score:** {score_delta.before} → {score_delta.after} ({sign}{score_delta.delta})")
            lines.append("")

        if not filtered:
            lines.append("_No user-facing changes._")
            lines.append("")
        else:
            groups: dict[str, list[str]] = {}
            for commit in filtered:
                prefix = _detect_prefix(commit.message)
                group_name = _CC_PREFIXES.get(prefix, "Changes")
                if group_name not in groups:
                    groups[group_name] = []
                groups[group_name].append(_clean_message(commit.message))

            order = ["Features", "Bug Fixes", "Performance", "Documentation",
                     "Refactoring", "Changes"]
            for group in order:
                if group not in groups:
                    continue
                lines.append(f"### {group}")
                lines.append("")
                for msg in groups[group]:
                    lines.append(f"- {msg}")
                lines.append("")

        # pip install command
        if version:
            pkg_ver = version.lstrip("v")
            lines.append("---")
            lines.append("")
            lines.append(f"```bash")
            lines.append(f"pip install agentkit-cli=={pkg_ver}")
            lines.append(f"```")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def write_github_step_summary(content: str) -> bool:
        """Append content to GITHUB_STEP_SUMMARY if env var is set.

        Returns True if written, False otherwise.
        """
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if not summary_path:
            return False
        try:
            with open(summary_path, "a", encoding="utf-8") as f:
                f.write("\n")
                f.write(content)
                f.write("\n")
            return True
        except OSError:
            return False

    @staticmethod
    def create_github_release(version: str, body: str, repo_path: str = ".") -> bool:
        """Create a GitHub release using the `gh` CLI.

        Only runs when explicitly called. Returns True on success.
        """
        try:
            result = subprocess.run(
                ["gh", "release", "create", version, "--notes", body],
                capture_output=True,
                text=True,
                cwd=repo_path,
                timeout=60,
            )
            return result.returncode == 0
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_ts(ts_str: str) -> datetime:
    """Parse ISO timestamp string to aware datetime."""
    try:
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        return datetime.fromisoformat(ts_str)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)
