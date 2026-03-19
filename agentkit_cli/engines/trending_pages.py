"""agentkit TrendingPagesEngine — fetch trending repos, score them, publish to GitHub Pages."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class TrendingPagesResult:
    pages_url: str
    repos_scored: int
    period: str
    language: Optional[str]
    published: bool
    error: Optional[str] = None
    leaderboard_json: Optional[dict] = None
    share_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Scoring helpers (mirrors daily_leaderboard pattern)
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
    return {
        "A": "#4ade80",
        "B": "#86efac",
        "C": "#fde68a",
        "D": "#fca5a5",
        "F": "#f87171",
    }.get(grade, "#d1d5db")


def _score_repo(repo: dict) -> tuple[float, str]:
    """Lightweight agentkit scoring heuristic. Returns (score, top_finding)."""
    score = 50.0
    finding = "Basic repo structure"

    stars = repo.get("stars", 0)
    if stars >= 10000:
        score += 20.0
        finding = "Highly popular repository"
    elif stars >= 1000:
        score += 10.0
        finding = "Strong community traction"

    lang = (repo.get("language") or "").lower()
    if lang == "python":
        score += 10.0
        finding = "Python — strong agent ecosystem fit"
    elif lang in ("typescript", "javascript"):
        score += 5.0

    desc = (repo.get("description") or "").lower()
    agent_keywords = ["agent", "llm", "gpt", "ai", "openai", "anthropic", "langchain", "rag", "embedding"]
    if any(kw in desc for kw in agent_keywords):
        score += 15.0
        finding = "Agent/LLM keyword in description"

    return min(score, 100.0), finding


# ---------------------------------------------------------------------------
# HTML / JSON generation
# ---------------------------------------------------------------------------

def generate_trending_html(
    repos: list[dict],
    period: str,
    language: Optional[str],
    scan_date: str,
) -> str:
    """Generate dark-theme responsive trending leaderboard HTML."""
    lang_label = f" · {language}" if language else ""
    title = f"AI-Ready Repos Today — Trending GitHub Leaderboard"
    subtitle = f"period: {period}{lang_label} · {scan_date} · powered by agentkit"

    scored_repos = [r for r in repos if r.get("agentkit_score") is not None]
    avg_score = (
        sum(r["agentkit_score"] for r in scored_repos) / len(scored_repos) if scored_repos else 0.0
    )
    top_repo = repos[0].get("full_name", "") if repos else ""

    rows_html = ""
    for r in repos:
        score = r.get("agentkit_score")
        grade = r.get("grade") or _score_to_grade(score)
        score_str = f"{score:.1f}" if score is not None else "—"
        grade_color = _grade_color(grade)
        full_name = r.get("full_name", "")
        repo_url = r.get("url") or f"https://github.com/{full_name}"
        description = (r.get("description") or "")[:120]
        stars = r.get("stars", 0)
        language_str = r.get("language") or ""
        finding = (r.get("top_finding") or "")[:80]
        rank = r.get("rank", "")
        rows_html += f"""
        <tr>
          <td style="color:#9ca3af;text-align:center">{rank}</td>
          <td>
            <a href="{repo_url}" target="_blank" style="color:#60a5fa;text-decoration:none;font-weight:600">{full_name}</a>
            <br><span style="color:#6b7280;font-size:0.8em">{description}</span>
          </td>
          <td style="color:#e5e7eb;text-align:right">{stars:,}</td>
          <td style="color:#9ca3af;text-align:center">{language_str}</td>
          <td style="color:#e5e7eb;text-align:right;font-weight:600">{score_str}</td>
          <td style="color:{grade_color};font-weight:700;text-align:center;font-size:1.1em">{grade}</td>
          <td style="color:#6b7280;font-size:0.8em">{finding}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="description" content="Daily leaderboard of AI-ready trending GitHub repositories scored by agentkit. Updated every day at 8 AM UTC."/>
<meta property="og:title" content="AI-Ready Repos Today"/>
<meta property="og:description" content="Daily trending GitHub repos ranked by agent-readiness score — {scan_date}"/>
<title>{title}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#111827;color:#f9fafb;font-family:system-ui,-apple-system,sans-serif;padding:2rem;max-width:1100px;margin:0 auto}}
  h1{{font-size:1.75rem;font-weight:700;margin-bottom:.3rem;background:linear-gradient(135deg,#60a5fa,#4ade80);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
  .subtitle{{color:#9ca3af;font-size:.9rem;margin-bottom:1.5rem}}
  .stats-bar{{display:flex;gap:2rem;background:#1f2937;border-radius:.5rem;padding:1rem 1.5rem;margin-bottom:1.5rem;flex-wrap:wrap;align-items:center}}
  .stat{{display:flex;flex-direction:column}}
  .stat-label{{font-size:.7rem;color:#6b7280;text-transform:uppercase;letter-spacing:.05em}}
  .stat-value{{font-size:1.1rem;font-weight:700;color:#e5e7eb}}
  .subscribe-cta{{margin-left:auto;background:#1e3a5f;border:1px solid #3b82f6;border-radius:.4rem;padding:.6rem 1.2rem;color:#93c5fd;font-size:.85rem}}
  .subscribe-cta a{{color:#60a5fa}}
  table{{width:100%;border-collapse:collapse;background:#1f2937;border-radius:.5rem;overflow:hidden}}
  th{{background:#374151;color:#9ca3af;font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;padding:.75rem 1rem;text-align:left}}
  td{{padding:.6rem 1rem;border-top:1px solid #374151;vertical-align:middle}}
  tr:hover td{{background:#252d3d}}
  .badge{{display:inline-block;background:#0d3f24;color:#4ade80;border-radius:.25rem;padding:.1rem .4rem;font-size:.7rem;font-weight:700}}
  footer{{margin-top:2rem;color:#4b5563;font-size:.75rem;text-align:center}}
  footer a{{color:#6b7280}}
  @media(max-width:700px){{.stats-bar{{gap:1rem}}.subscribe-cta{{margin-left:0}}td,th{{padding:.4rem .6rem}}}}
</style>
</head>
<body>
<h1>🤖 AI-Ready Repos Today</h1>
<div class="subtitle">Trending GitHub repositories scored for agent-readiness · {subtitle}</div>
<div class="stats-bar">
  <div class="stat"><span class="stat-label">Repos Ranked</span><span class="stat-value">{len(repos)}</span></div>
  <div class="stat"><span class="stat-label">Avg Score</span><span class="stat-value">{avg_score:.1f}</span></div>
  <div class="stat"><span class="stat-label">Top Repo</span><span class="stat-value" style="font-size:.9rem">{top_repo}</span></div>
  <div class="stat"><span class="stat-label">Updated</span><span class="stat-value" style="font-size:.85rem">{scan_date}</span></div>
  <div class="subscribe-cta">
    ⭐ Subscribe to daily AI-ready repos: <a href="https://github.com/mikiships/agentkit-trending" target="_blank">mikiships/agentkit-trending</a>
  </div>
</div>
<table>
<thead>
  <tr>
    <th style="width:2.5rem;text-align:center">#</th>
    <th>Repository</th>
    <th style="text-align:right">Stars</th>
    <th style="text-align:center">Lang</th>
    <th style="text-align:right">Score</th>
    <th style="text-align:center">Grade</th>
    <th>Top Signal</th>
  </tr>
</thead>
<tbody>{rows_html}
</tbody>
</table>
<footer>
  <p>Generated {scan_date} by <a href="https://pypi.org/project/agentkit-cli/">agentkit-cli</a> ·
  <a href="leaderboard.json">JSON data</a> ·
  Scores reflect agent-readiness heuristics (stars, language, description keywords)</p>
</footer>
</body>
</html>"""
    return html


def generate_leaderboard_json(
    repos: list[dict],
    period: str,
    language: Optional[str],
    scan_date: str,
) -> dict:
    """Generate structured JSON for the trending leaderboard."""
    return {
        "generated": scan_date,
        "period": period,
        "language": language,
        "repos": [
            {
                "rank": r.get("rank"),
                "full_name": r.get("full_name", ""),
                "stars": r.get("stars", 0),
                "language": r.get("language", ""),
                "agentkit_score": r.get("agentkit_score"),
                "grade": r.get("grade") or _score_to_grade(r.get("agentkit_score")),
                "top_finding": r.get("top_finding", ""),
                "url": r.get("url", ""),
            }
            for r in repos
        ],
    }


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def _strip_dot_git(s: str) -> str:
    return s[:-4] if s.endswith(".git") else s


def _parse_pages_url(pages_repo: str, filename: str = "trending.html") -> str:
    """Build a GitHub Pages URL from owner/repo and filename."""
    parts = pages_repo.split("/", 1)
    if len(parts) == 2:
        owner, repo = parts[0], parts[1]
        return f"https://{owner}.github.io/{repo}/{filename}"
    return f"https://{pages_repo}.github.io/{filename}"


def _clone_or_pull_pages_repo(
    pages_repo: str,
    clone_dir: Path,
    pages_branch: str,
    token: Optional[str] = None,
) -> tuple[bool, str]:
    """Clone or update the Pages target repo. Returns (success, error_msg)."""
    resolved_token = token or os.environ.get("GITHUB_TOKEN")
    if resolved_token:
        remote_url = f"https://{resolved_token}@github.com/{pages_repo}.git"
    else:
        remote_url = f"https://github.com/{pages_repo}.git"

    if clone_dir.exists() and (clone_dir / ".git").exists():
        result = subprocess.run(
            ["git", "pull", "--rebase", "origin", pages_branch],
            cwd=str(clone_dir),
            capture_output=True,
        )
        return result.returncode == 0, ""
    else:
        clone_dir.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", "--branch", pages_branch, "--depth", "1", remote_url, str(clone_dir)],
            capture_output=True,
        )
        if result.returncode != 0:
            result2 = subprocess.run(
                ["git", "clone", remote_url, str(clone_dir)],
                capture_output=True,
            )
            if result2.returncode != 0:
                stderr = result2.stderr.decode("utf-8", errors="replace").strip()
                return False, stderr or "git clone failed"
        return True, ""


def _commit_and_push(
    repo_root: Path,
    files: list[Path],
    commit_msg: str,
    pages_branch: str,
) -> tuple[bool, str]:
    """Stage, commit, push given files. Returns (success, error_msg)."""
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
# TrendingPagesEngine
# ---------------------------------------------------------------------------

class TrendingPagesEngine:
    """Fetch trending GitHub repos, score them with agentkit, publish leaderboard to Pages."""

    def __init__(
        self,
        pages_repo: str,
        limit: int = 20,
        language: Optional[str] = None,
        period: str = "today",
        pages_branch: str = "main",
        pages_path: str = "docs/",
        dry_run: bool = False,
        share: bool = False,
        token: Optional[str] = None,
        _prefetched_repos: Optional[list[dict]] = None,
    ) -> None:
        self.pages_repo = pages_repo
        self.limit = min(max(1, limit), 50)
        self.language = language
        self.period = period
        self.pages_branch = pages_branch
        self.pages_path = pages_path.rstrip("/") + "/"
        self.dry_run = dry_run
        self.share = share
        self.token = token or os.environ.get("GITHUB_TOKEN")
        # Allow injection for testing
        self._prefetched_repos = _prefetched_repos

    def _fetch_repos(self) -> list[dict]:
        """Fetch trending repos via the existing trending infrastructure."""
        from agentkit_cli.trending import fetch_trending

        period_map = {"today": 1, "week": 7, "month": 30}
        days = period_map.get(self.period, 1)

        try:
            repos = fetch_trending(
                period=self.period,
                topic=self.language,
                limit=self.limit,
                token=self.token,
            )
        except Exception:
            repos = []

        # Normalize
        normalized = []
        for r in repos:
            normalized.append({
                "full_name": r.get("full_name", ""),
                "description": r.get("description", ""),
                "stars": r.get("stars", 0),
                "language": r.get("language", ""),
                "url": r.get("url", f"https://github.com/{r.get('full_name', '')}"),
            })
        return normalized

    def _score_repos(self, repos: list[dict]) -> list[dict]:
        """Score repos and return them with agentkit_score + top_finding."""
        scored = []
        for repo in repos:
            # Skip repos with empty full_name
            if not repo.get("full_name"):
                continue
            agentkit_score, top_finding = _score_repo(repo)
            scored.append({
                **repo,
                "agentkit_score": agentkit_score,
                "grade": _score_to_grade(agentkit_score),
                "top_finding": top_finding,
            })
        # Sort by score descending
        scored.sort(key=lambda r: -(r.get("agentkit_score") or 0))
        for i, r in enumerate(scored, start=1):
            r["rank"] = i
        return scored

    def run(self, clone_dir: Optional[Path] = None) -> TrendingPagesResult:
        """Main entry point: fetch, score, generate, optionally publish."""
        scan_date = datetime.now(timezone.utc).date().isoformat()

        # 1. Fetch
        raw_repos = self._prefetched_repos if self._prefetched_repos is not None else self._fetch_repos()

        # 2. Score
        repos = self._score_repos(raw_repos)

        repos_scored = len(repos)
        pages_url = _parse_pages_url(self.pages_repo, "trending.html")

        # 3. Generate HTML + JSON
        if repos:
            html = generate_trending_html(
                repos=repos,
                period=self.period,
                language=self.language,
                scan_date=scan_date,
            )
            leaderboard_json = generate_leaderboard_json(
                repos=repos,
                period=self.period,
                language=self.language,
                scan_date=scan_date,
            )
        else:
            # Empty results — generate minimal page
            html = generate_trending_html(
                repos=[],
                period=self.period,
                language=self.language,
                scan_date=scan_date,
            )
            leaderboard_json = generate_leaderboard_json(
                repos=[],
                period=self.period,
                language=self.language,
                scan_date=scan_date,
            )

        if self.dry_run:
            return TrendingPagesResult(
                pages_url=pages_url,
                repos_scored=repos_scored,
                period=self.period,
                language=self.language,
                published=False,
                leaderboard_json=leaderboard_json,
            )

        # 4. Clone/pull
        if clone_dir is None:
            _tmp = tempfile.mkdtemp(prefix="agentkit-trending-pages-")
            clone_dir = Path(_tmp)

        ok, err = _clone_or_pull_pages_repo(
            pages_repo=self.pages_repo,
            clone_dir=clone_dir,
            pages_branch=self.pages_branch,
            token=self.token,
        )

        if not ok:
            return TrendingPagesResult(
                pages_url=pages_url,
                repos_scored=repos_scored,
                period=self.period,
                language=self.language,
                published=False,
                error=err or "git clone/pull failed",
                leaderboard_json=leaderboard_json,
            )

        # 5. Write files
        out_dir = clone_dir / self.pages_path.lstrip("/")
        out_dir.mkdir(parents=True, exist_ok=True)
        html_file = out_dir / "trending.html"
        json_file = out_dir / "leaderboard.json"
        html_file.write_text(html, encoding="utf-8")
        json_file.write_text(json.dumps(leaderboard_json, indent=2), encoding="utf-8")

        # 6. Commit + push
        commit_msg = f"chore: update trending leaderboard {scan_date} [skip ci]"
        pushed, push_err = _commit_and_push(
            repo_root=clone_dir,
            files=[html_file, json_file],
            commit_msg=commit_msg,
            pages_branch=self.pages_branch,
        )

        # 7. Optional share to here.now
        share_url: Optional[str] = None
        if self.share and pushed:
            try:
                from agentkit_cli.publish import upload_html
                share_url = upload_html(html)
            except Exception:
                pass

        return TrendingPagesResult(
            pages_url=pages_url,
            repos_scored=repos_scored,
            period=self.period,
            language=self.language,
            published=pushed,
            error=push_err if not pushed else None,
            leaderboard_json=leaderboard_json,
            share_url=share_url,
        )
