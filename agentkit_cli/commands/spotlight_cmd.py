"""agentkit spotlight — Repo of the Day: pick, analyze, and share a trending repo."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agentkit_cli import __version__
from agentkit_cli.trending import fetch_trending, fetch_popular

console = Console()


# ---------------------------------------------------------------------------
# SpotlightResult dataclass
# ---------------------------------------------------------------------------

@dataclass
class SpotlightResult:
    repo: str                            # "owner/repo"
    score: Optional[float]
    grade: Optional[str]
    top_findings: list[str]
    run_date: str                        # ISO UTC
    redteam_resistance: Optional[float] = None
    cert_id: Optional[str] = None
    share_url: Optional[str] = None
    repo_description: str = ""
    repo_stars: int = 0
    repo_language: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# SpotlightEngine
# ---------------------------------------------------------------------------

class SpotlightEngine:
    """Core engine for selecting and analyzing spotlight repos."""

    HISTORY_KEY = "spotlight"

    def __init__(self, db=None):
        self._db = db  # HistoryDB or None (lazy)

    def _get_db(self):
        if self._db is None:
            from agentkit_cli.history import HistoryDB
            self._db = HistoryDB()
        return self._db

    def _already_spotlighted(self, full_name: str) -> bool:
        """Check if this repo was recently spotlighted (last 30 runs)."""
        try:
            db = self._get_db()
            rows = db.get_history(project=f"spotlight:{full_name}", tool="spotlight", limit=1)
            return len(rows) > 0
        except Exception:
            return False

    def select_candidate(
        self,
        topic: Optional[str] = None,
        language: Optional[str] = None,
        token: Optional[str] = None,
    ) -> Optional[dict]:
        """Return the first trending repo not yet spotlighted today.

        Falls back to fetch_popular if token not available.
        Returns a dict with full_name, description, stars, language, url.
        """
        resolved_token = token or os.environ.get("GITHUB_TOKEN")

        # Build topic/lang query
        q_topic = topic
        q_lang = language

        try:
            if q_topic:
                repos = fetch_trending(period="week", topic=q_topic, limit=10, token=resolved_token)
            elif q_lang:
                repos = fetch_trending(period="week", topic=q_lang, limit=10, token=resolved_token)
            else:
                repos = fetch_trending(period="day", category="ai", limit=15, token=resolved_token)

            if not repos:
                repos = fetch_popular(limit=10, token=resolved_token)
        except Exception:
            repos = []

        for repo in repos:
            full_name = repo.get("full_name", "")
            if full_name and not self._already_spotlighted(full_name):
                return repo

        # All were spotlighted or list empty — return first anyway
        if repos:
            return repos[0]

        return None

    def _score_to_grade(self, score: Optional[float]) -> Optional[str]:
        if score is None:
            return None
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    def _extract_findings(self, result) -> list[str]:
        """Pull top findings from an AnalyzeResult."""
        findings: list[str] = []
        for tool_name, info in (result.tools or {}).items():
            finding = info.get("finding", "")
            if finding and finding not in ("", "N/A"):
                findings.append(f"[{tool_name}] {finding}")
            if len(findings) >= 5:
                break
        return findings[:5]

    def run_spotlight(
        self,
        repo: str,
        deep: bool = False,
        token: Optional[str] = None,
        no_history: bool = False,
    ) -> SpotlightResult:
        """Run analyze (+ optionally redteam + certify) on a repo.

        repo: "owner/repo" or "github:owner/repo"
        """
        if not repo.startswith("github:"):
            target = f"github:{repo}"
        else:
            target = repo
            repo = repo.removeprefix("github:")

        run_date = datetime.now(timezone.utc).isoformat()

        # ---- Analyze ----
        score: Optional[float] = None
        grade: Optional[str] = None
        top_findings: list[str] = []
        redteam_resistance: Optional[float] = None
        cert_id: Optional[str] = None

        try:
            from agentkit_cli.analyze import analyze_target
            analyze_result = analyze_target(
                target=target,
                keep=False,
                publish=False,
                timeout=120,
                no_generate=True,
            )
            score = analyze_result.composite_score
            grade = self._score_to_grade(score)
            top_findings = self._extract_findings(analyze_result)
        except Exception as exc:
            console.print(f"[dim]Analyze failed: {exc}[/dim]")

        # ---- Deep: redteam + certify ----
        if deep:
            try:
                from agentkit_cli.redteam import RedTeamEngine
                rt_engine = RedTeamEngine()
                rt_result = rt_engine.run(target=target, attacks_per_category=3)
                redteam_resistance = getattr(rt_result, "resistance_score", None)
            except Exception as exc:
                console.print(f"[dim]RedTeam failed: {exc}[/dim]")

            try:
                from agentkit_cli.certify import CertEngine
                cert_engine = CertEngine()
                cert_result = cert_engine.certify(
                    target=target,
                    composite_score=int(score or 0),
                    redteam_score=int(redteam_resistance or 0),
                    freshness_score=70,
                )
                cert_id = cert_result.cert_id
            except Exception as exc:
                console.print(f"[dim]Certify failed: {exc}[/dim]")

        # ---- Fetch repo metadata ----
        repo_description = ""
        repo_stars = 0
        repo_language = ""
        try:
            import urllib.request
            headers = {"Accept": "application/vnd.github+json"}
            gh_token = token or os.environ.get("GITHUB_TOKEN")
            if gh_token:
                headers["Authorization"] = f"Bearer {gh_token}"
            req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}",
                headers=headers,
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                repo_description = data.get("description") or ""
                repo_stars = data.get("stargazers_count", 0)
                repo_language = data.get("language") or ""
        except Exception:
            pass

        result = SpotlightResult(
            repo=repo,
            score=score,
            grade=grade,
            top_findings=top_findings,
            run_date=run_date,
            redteam_resistance=redteam_resistance,
            cert_id=cert_id,
            repo_description=repo_description,
            repo_stars=repo_stars,
            repo_language=repo_language,
        )

        # ---- Record to history ----
        if not no_history:
            try:
                db = self._get_db()
                db.record_run(
                    project=f"spotlight:{repo}",
                    tool="spotlight",
                    score=score or 0.0,
                    details={
                        "grade": grade,
                        "top_findings": top_findings,
                        "redteam_resistance": redteam_resistance,
                        "cert_id": cert_id,
                        "share_url": None,
                    },
                    label="spotlight",
                )
            except Exception as exc:
                console.print(f"[dim]History record failed: {exc}[/dim]")

        return result


# ---------------------------------------------------------------------------
# CLI command function
# ---------------------------------------------------------------------------

def _build_spotlight_tweet(result: "SpotlightResult") -> str:
    """Build tweet text for a spotlight result. ≤280 chars."""
    score_str = f"{result.score:.0f}/100" if result.score is not None else "N/A"
    # Pick first finding as key insight (strip tool prefix if present)
    finding = ""
    if result.top_findings:
        raw = result.top_findings[0]
        # Strip "[toolname] " prefix if present
        if raw.startswith("[") and "] " in raw:
            finding = raw.split("] ", 1)[1]
        else:
            finding = raw
    # Base: "owner/repo scores N/100. <finding>."
    base = f"{result.repo} scores {score_str}."
    if finding:
        candidate = f"{base} {finding}"
        if not candidate.endswith("."):
            candidate += "."
    else:
        candidate = base
    # Enforce ≤280 (leave room for URL if share)
    if len(candidate) > 280:
        max_len = 277
        candidate = candidate[:max_len] + "..."
    return candidate


def spotlight_command(
    target: Optional[str],
    topic: Optional[str],
    language: Optional[str],
    deep: bool,
    share: bool,
    json_output: bool,
    output: Optional[str],
    quiet: bool,
    no_history: bool,
    tweet_only: bool = False,
    db_path=None,
) -> None:
    """Select or analyze a repo spotlight, generate a report."""
    engine = SpotlightEngine(db=db_path)

    # Select repo
    repo: Optional[str] = None
    repo_meta: dict = {}
    if target:
        # Explicit repo provided
        if target.startswith("github:"):
            repo = target.removeprefix("github:")
        else:
            repo = target
    else:
        if not quiet and not tweet_only:
            console.print("\n[bold]agentkit spotlight[/bold] — selecting today's repo…")
        candidate = engine.select_candidate(topic=topic, language=language)
        if not candidate:
            console.print("[red]No candidate repo found.[/red]")
            raise typer.Exit(code=1)
        repo = candidate["full_name"]
        repo_meta = candidate

    if not quiet and not json_output and not tweet_only:
        console.print(f"\n[bold cyan]Spotlight:[/bold cyan] {repo}")

    # Run
    result = engine.run_spotlight(repo=repo, deep=deep, no_history=no_history)

    # Share
    if share:
        from agentkit_cli.renderers.spotlight_renderer import SpotlightHTMLRenderer
        renderer = SpotlightHTMLRenderer()
        html = renderer.render(result)
        url = _upload_spotlight(html, repo.replace("/", "-") + "-spotlight.html")
        result.share_url = url
        if url and not quiet:
            console.print(f"\n[green]Share URL:[/green] {url}")

        # Update history with share_url
        if not no_history:
            try:
                db = engine._get_db()
                db.record_run(
                    project=f"spotlight:{repo}",
                    tool="spotlight_share",
                    score=result.score or 0.0,
                    details={"share_url": url},
                    label="spotlight",
                )
            except Exception:
                pass

    # Handle --tweet-only: output clean tweet text to stdout, nothing else
    if tweet_only:
        tweet_text = _build_spotlight_tweet(result)
        if result.share_url:
            candidate = f"{tweet_text} {result.share_url}"
            if len(candidate) <= 280:
                tweet_text = candidate
        print(tweet_text)
        return

    # Output
    if json_output:
        out = result.to_dict()
        if output:
            with open(output, "w") as f:
                json.dump(out, f, indent=2)
        else:
            print(json.dumps(out, indent=2))
        return

    if output:
        from agentkit_cli.renderers.spotlight_renderer import SpotlightHTMLRenderer
        renderer = SpotlightHTMLRenderer()
        html = renderer.render(result)
        with open(output, "w") as f:
            f.write(html)
        if not quiet:
            console.print(f"[green]Report written to:[/green] {output}")
        return

    if quiet:
        return

    # Rich terminal output
    _print_result(result)


def _print_result(result: SpotlightResult) -> None:
    grade_color = {"A": "green", "B": "green", "C": "yellow", "D": "red", "F": "red"}.get(
        result.grade or "", "dim"
    )
    score_str = f"{result.score:.1f}" if result.score is not None else "N/A"
    grade_str = result.grade or "?"

    console.print(
        Panel(
            f"[bold]{result.repo}[/bold]\n"
            f"Score: [{grade_color}]{score_str}[/{grade_color}]  Grade: [{grade_color}]{grade_str}[/{grade_color}]\n"
            + (f"Stars: {result.repo_stars}  Language: {result.repo_language}\n" if result.repo_stars else "")
            + (f"{result.repo_description}\n" if result.repo_description else ""),
            title="[bold]Repo Spotlight[/bold]",
            border_style="cyan",
        )
    )

    if result.top_findings:
        console.print("\n[bold]Top Findings:[/bold]")
        for i, f in enumerate(result.top_findings[:3], 1):
            console.print(f"  {i}. {f}")

    if result.redteam_resistance is not None:
        console.print(f"\n[bold]RedTeam Resistance:[/bold] {result.redteam_resistance:.1f}")

    if result.cert_id:
        console.print(f"[bold]Cert ID:[/bold] {result.cert_id}")

    if result.share_url:
        console.print(f"\n[bold green]Share URL:[/bold green] {result.share_url}")


def _upload_spotlight(html_content: str, filename: str) -> Optional[str]:
    """Upload spotlight HTML to here.now. Returns URL or None."""
    api_key = os.environ.get("HERENOW_API_KEY", "")
    if not api_key:
        return None
    try:
        import urllib.request
        body = json.dumps({"files": [{"name": filename, "content_type": "text/html"}]}).encode()
        req = urllib.request.Request(
            "https://here.now/api/v1/publish",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            publish_data = json.loads(resp.read())

        upload_url = publish_data["files"][0]["upload_url"]
        final_url = publish_data.get("url") or publish_data.get("site_url", "")
        site_id = publish_data.get("site_id") or publish_data.get("id", "")

        put_req = urllib.request.Request(
            upload_url,
            data=html_content.encode(),
            headers={"Content-Type": "text/html"},
            method="PUT",
        )
        with urllib.request.urlopen(put_req, timeout=30):
            pass

        if site_id:
            fin_body = json.dumps({"site_id": site_id}).encode()
            fin_req = urllib.request.Request(
                "https://here.now/api/v1/finalize",
                data=fin_body,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(fin_req, timeout=30) as resp:
                    fin_data = json.loads(resp.read())
                    final_url = fin_data.get("url") or final_url
            except Exception:
                pass

        return final_url or None
    except Exception as exc:
        console.print(f"[yellow]Share upload failed: {exc}[/yellow]")
        return None
