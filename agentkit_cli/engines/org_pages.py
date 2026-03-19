"""agentkit org-pages engine — score all public repos in a GitHub org and publish to GitHub Pages."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class OrgPagesResult:
    pages_url: str
    repos_scored: int
    avg_score: float
    top_repo: str
    published: bool
    error: Optional[str] = None
    leaderboard_json: Optional[dict] = None


# ---------------------------------------------------------------------------
# HTML / JSON generation
# ---------------------------------------------------------------------------

def _score_to_grade(score: Optional[float]) -> str:
    if score is None:
        return "F"
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _grade_color(grade: str) -> str:
    return {"A": "#4ade80", "B": "#86efac", "C": "#fde68a", "D": "#fca5a5", "F": "#f87171"}.get(grade, "#d1d5db")


def generate_org_html(
    org: str,
    scan_date: str,
    repos: list[dict],
    avg_score: float,
    top_repo: str,
) -> str:
    """Generate dark-theme responsive HTML org leaderboard."""

    rows_html = ""
    for r in repos:
        score = r.get("score")
        grade = r.get("grade") or _score_to_grade(score)
        score_str = f"{score:.1f}" if score is not None else "—"
        grade_color = _grade_color(grade)
        finding = r.get("top_finding", "") or ""
        full_name = r.get("full_name", r.get("repo", ""))
        repo_url = f"https://github.com/{full_name}"
        last_analyzed = r.get("analyzed_at", scan_date)
        rank = r.get("rank", "")
        rows_html += f"""
        <tr>
          <td style="color:#9ca3af">{rank}</td>
          <td><a href="{repo_url}" target="_blank" style="color:#60a5fa;text-decoration:none">{full_name}</a></td>
          <td style="color:#e5e7eb;text-align:right">{score_str}</td>
          <td style="color:{grade_color};font-weight:700;text-align:center">{grade}</td>
          <td style="color:#9ca3af;font-size:0.85em">{finding[:80]}</td>
          <td style="color:#6b7280;font-size:0.8em">{last_analyzed}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{org} — Agent-Readiness Leaderboard</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#111827;color:#f9fafb;font-family:system-ui,-apple-system,sans-serif;padding:2rem}}
  h1{{font-size:1.75rem;font-weight:700;margin-bottom:.25rem}}
  .subtitle{{color:#9ca3af;font-size:.9rem;margin-bottom:2rem}}
  .stats-bar{{display:flex;gap:2rem;background:#1f2937;border-radius:.5rem;padding:1rem 1.5rem;margin-bottom:2rem;flex-wrap:wrap}}
  .stat{{display:flex;flex-direction:column}}
  .stat-label{{font-size:.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:.05em}}
  .stat-value{{font-size:1.25rem;font-weight:700;color:#e5e7eb}}
  table{{width:100%;border-collapse:collapse;background:#1f2937;border-radius:.5rem;overflow:hidden}}
  th{{background:#374151;color:#9ca3af;font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;padding:.75rem 1rem;text-align:left}}
  td{{padding:.65rem 1rem;border-top:1px solid #374151;vertical-align:top}}
  tr:hover td{{background:#252d3d}}
  @media(max-width:600px){{.stats-bar{{gap:1rem}}.stat-value{{font-size:1rem}}td,th{{padding:.5rem .6rem}}}}
</style>
</head>
<body>
<h1>🏆 {org} — Org Leaderboard</h1>
<div class="subtitle">Agent-readiness scores · scanned {scan_date} · powered by <strong>agentkit</strong></div>
<div class="stats-bar">
  <div class="stat"><span class="stat-label">Repos Scored</span><span class="stat-value">{len(repos)}</span></div>
  <div class="stat"><span class="stat-label">Avg Score</span><span class="stat-value">{avg_score:.1f}</span></div>
  <div class="stat"><span class="stat-label">Top Scorer</span><span class="stat-value" style="font-size:.9rem">{top_repo}</span></div>
</div>
<table>
<thead>
  <tr>
    <th style="width:2rem">#</th>
    <th>Repo</th>
    <th style="text-align:right">Score</th>
    <th style="text-align:center">Grade</th>
    <th>Top Finding</th>
    <th>Analyzed</th>
  </tr>
</thead>
<tbody>{rows_html}
</tbody>
</table>
<p style="margin-top:1.5rem;color:#4b5563;font-size:.8rem">Generated {scan_date} by <a href="https://pypi.org/project/agentkit-cli/" style="color:#6b7280">agentkit-cli</a></p>
</body>
</html>"""
    return html


def generate_leaderboard_json(
    org: str,
    scan_date: str,
    repos: list[dict],
) -> dict:
    """Generate structured JSON for the org leaderboard."""
    return {
        "org": org,
        "scan_date": scan_date,
        "repos": [
            {
                "name": r.get("full_name", r.get("repo", "")),
                "score": r.get("score"),
                "grade": r.get("grade") or _score_to_grade(r.get("score")),
                "top_finding": r.get("top_finding", ""),
            }
            for r in repos
        ],
    }


# ---------------------------------------------------------------------------
# Git helpers (mirrors daily_leaderboard.py pattern)
# ---------------------------------------------------------------------------

def _strip_dot_git(s: str) -> str:
    return s[:-4] if s.endswith(".git") else s


def _parse_pages_url(remote_url: str, pages_path: str) -> str:
    """Convert git remote URL to GitHub Pages URL."""
    remote = remote_url.strip()
    if remote.startswith("git@github.com:"):
        owner_repo = _strip_dot_git(remote[len("git@github.com:"):].rstrip("/"))
    elif "github.com/" in remote:
        owner_repo = _strip_dot_git(remote.split("github.com/", 1)[1].rstrip("/"))
    else:
        owner_repo = _strip_dot_git(remote)

    parts = owner_repo.split("/", 1)
    if len(parts) == 2:
        owner, repo = parts[0], parts[1]
        return f"https://{owner}.github.io/{repo}/"
    return f"https://{owner_repo}.github.io/"


def _clone_or_pull_pages_repo(
    pages_repo: str,
    clone_dir: Path,
    pages_branch: str,
    token: Optional[str] = None,
) -> tuple[bool, str]:
    """Clone or pull the Pages repo. Returns (success, remote_url)."""
    # Build authenticated URL
    resolved_token = token or os.environ.get("GITHUB_TOKEN")
    if resolved_token:
        remote_url = f"https://{resolved_token}@github.com/{pages_repo}.git"
    else:
        remote_url = f"https://github.com/{pages_repo}.git"

    plain_remote = f"https://github.com/{pages_repo}.git"

    if clone_dir.exists() and (clone_dir / ".git").exists():
        # Pull
        result = subprocess.run(
            ["git", "pull", "--rebase", "origin", pages_branch],
            cwd=str(clone_dir),
            capture_output=True,
        )
        return result.returncode == 0, plain_remote
    else:
        clone_dir.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", "--branch", pages_branch, "--depth", "1", remote_url, str(clone_dir)],
            capture_output=True,
        )
        if result.returncode != 0:
            # Try without specifying branch (repo may be empty)
            result2 = subprocess.run(
                ["git", "clone", remote_url, str(clone_dir)],
                capture_output=True,
            )
            return result2.returncode == 0, plain_remote
        return True, plain_remote


def _commit_and_push(
    repo_root: Path,
    files: list[Path],
    commit_msg: str,
    pages_branch: str,
) -> tuple[bool, str]:
    """Stage, commit, push files. Returns (success, error_msg)."""
    try:
        subprocess.run(
            ["git", "add"] + [str(f) for f in files],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "push", "origin", pages_branch],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
        )
        return True, ""
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
        return False, stderr.strip() or str(exc)


# ---------------------------------------------------------------------------
# OrgPagesEngine
# ---------------------------------------------------------------------------

class OrgPagesEngine:
    """Score all public repos in a GitHub org and publish a leaderboard to GitHub Pages."""

    def __init__(
        self,
        org: str,
        pages_repo: Optional[str] = None,
        pages_path: str = "docs/",
        pages_branch: str = "main",
        token: Optional[str] = None,
        only_below: Optional[int] = None,
        limit: int = 50,
        dry_run: bool = False,
        _org_results: Optional[list[dict]] = None,
    ) -> None:
        self.org = org
        self.pages_repo = pages_repo or f"{org}/agentkit-scores"
        self.pages_path = pages_path.rstrip("/") + "/"
        self.pages_branch = pages_branch
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.only_below = only_below
        self.limit = limit
        self.dry_run = dry_run
        # Allow injecting pre-scored results (for testing / D3 integration)
        self._org_results = _org_results

    def _score_repos(self) -> list[dict]:
        """Use OrgCommand to score all public repos."""
        from agentkit_cli.commands.org_cmd import OrgCommand

        cmd = OrgCommand(
            owner=self.org,
            limit=self.limit,
            token=self.token,
            json_output=True,  # suppress rich output
        )
        result = cmd.run()
        ranked = result.get("ranked", [])
        # Assign analyzed_at
        now = datetime.now(timezone.utc).date().isoformat()
        for r in ranked:
            r.setdefault("analyzed_at", now)
        return ranked

    def run(self, clone_dir: Optional[Path] = None) -> OrgPagesResult:
        """Score repos and optionally publish to GitHub Pages."""
        # 1. Score repos
        ranked = self._org_results if self._org_results is not None else self._score_repos()

        # 2. Filter
        if self.only_below is not None:
            ranked = [r for r in ranked if (r.get("score") is None or r.get("score", 100) < self.only_below)]

        repos_scored = len(ranked)
        scored_repos = [r for r in ranked if r.get("score") is not None]
        avg_score = sum(r["score"] for r in scored_repos) / len(scored_repos) if scored_repos else 0.0
        top_repo = ranked[0].get("full_name", ranked[0].get("repo", "")) if ranked else ""

        scan_date = datetime.now(timezone.utc).date().isoformat()

        # 3. Generate HTML + JSON
        html = generate_org_html(
            org=self.org,
            scan_date=scan_date,
            repos=ranked,
            avg_score=avg_score,
            top_repo=top_repo,
        )
        leaderboard_json = generate_leaderboard_json(
            org=self.org,
            scan_date=scan_date,
            repos=ranked,
        )

        if self.dry_run:
            return OrgPagesResult(
                pages_url=f"https://{self.pages_repo.split('/')[0]}.github.io/agentkit-scores/",
                repos_scored=repos_scored,
                avg_score=avg_score,
                top_repo=top_repo,
                published=False,
                leaderboard_json=leaderboard_json,
            )

        # 4. Clone/pull pages repo
        if clone_dir is None:
            import tempfile
            _tmp = tempfile.mkdtemp(prefix="agentkit-org-pages-")
            clone_dir = Path(_tmp)

        ok, remote_url = _clone_or_pull_pages_repo(
            pages_repo=self.pages_repo,
            clone_dir=clone_dir,
            pages_branch=self.pages_branch,
            token=self.token,
        )

        pages_url = _parse_pages_url(remote_url, self.pages_path)

        if not ok:
            return OrgPagesResult(
                pages_url=pages_url,
                repos_scored=repos_scored,
                avg_score=avg_score,
                top_repo=top_repo,
                published=False,
                error="git clone/pull failed",
                leaderboard_json=leaderboard_json,
            )

        # 5. Write files
        out_dir = clone_dir / self.pages_path.lstrip("/")
        out_dir.mkdir(parents=True, exist_ok=True)
        html_file = out_dir / "index.html"
        json_file = out_dir / "leaderboard.json"
        html_file.write_text(html, encoding="utf-8")
        json_file.write_text(json.dumps(leaderboard_json, indent=2), encoding="utf-8")

        # 6. Commit + push
        pushed, err = _commit_and_push(
            repo_root=clone_dir,
            files=[html_file, json_file],
            commit_msg=f"chore: update org leaderboard for {self.org} [skip ci]",
            pages_branch=self.pages_branch,
        )

        return OrgPagesResult(
            pages_url=pages_url,
            repos_scored=repos_scored,
            avg_score=avg_score,
            top_repo=top_repo,
            published=pushed,
            error=err if not pushed else None,
            leaderboard_json=leaderboard_json,
        )
