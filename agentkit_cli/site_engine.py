"""agentkit site_engine — multi-page static site generator from history DB."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from agentkit_cli.history import HistoryDB
from agentkit_cli.user_scorecard import score_to_grade

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class PageMeta:
    title: str
    description: str
    canonical_url: str
    last_modified: str = ""


@dataclass
class SiteConfig:
    base_url: str = "https://mikiships.github.io/agentkit-cli/"
    topics: List[str] = field(default_factory=lambda: ["python", "typescript", "rust", "go"])
    limit: int = 20


@dataclass
class SitePage:
    path: str          # relative path within output dir, e.g. "index.html"
    html: str
    meta: PageMeta


@dataclass
class RepoEntry:
    repo: str          # owner/repo
    score: float
    grade: str
    last_run: str
    details: dict = field(default_factory=dict)


@dataclass
class SiteResult:
    pages: List[SitePage] = field(default_factory=list)
    sitemap_xml: str = ""
    share_url: Optional[str] = None


# ---------------------------------------------------------------------------
# CSS (dark theme — shared with leaderboard_page)
# ---------------------------------------------------------------------------

_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #0d1117;
    color: #e6edf3;
    font-family: 'Courier New', Courier, monospace;
    min-height: 100vh;
    padding: 0;
}
a { color: #58a6ff; text-decoration: none; }
a:hover { text-decoration: underline; }
header {
    background: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 1rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
header h1 { font-size: 1.2rem; color: #58a6ff; }
header nav a { margin-left: 1rem; font-size: 0.9rem; color: #8b949e; }
.container { max-width: 900px; margin: 0 auto; padding: 2rem 1rem; }
.hero {
    text-align: center;
    padding: 3rem 1rem 2rem;
}
.hero h2 { font-size: 2rem; color: #58a6ff; margin-bottom: 0.5rem; }
.hero p { color: #8b949e; font-size: 1rem; }
.stats {
    display: flex;
    gap: 1.5rem;
    justify-content: center;
    flex-wrap: wrap;
    margin: 1.5rem 0;
}
.stat-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    text-align: center;
    min-width: 130px;
}
.stat-card .value { font-size: 2rem; font-weight: bold; color: #58a6ff; }
.stat-card .label { font-size: 0.8rem; color: #8b949e; margin-top: 0.25rem; }
.topics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 1rem;
    margin: 2rem 0;
}
.topic-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 1.2rem;
    text-align: center;
}
.topic-card h3 { color: #58a6ff; font-size: 1rem; margin-bottom: 0.5rem; }
.topic-card p { color: #8b949e; font-size: 0.8rem; }
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5rem 0;
    font-size: 0.9rem;
}
th, td {
    padding: 0.6rem 0.8rem;
    border-bottom: 1px solid #30363d;
    text-align: left;
}
th { color: #8b949e; font-weight: normal; font-size: 0.8rem; }
tr:hover { background: #161b22; }
.badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-weight: bold;
    font-size: 0.85rem;
}
.badge-A { background: #1a7f37; color: #fff; }
.badge-B { background: #1c4fd6; color: #fff; }
.badge-C { background: #9a6700; color: #fff; }
.badge-D { background: #6e1c1c; color: #fff; }
.badge-F { background: #6e1c1c; color: #fff; }
.score-bar-wrap { background: #30363d; border-radius: 4px; height: 8px; width: 120px; display: inline-block; vertical-align: middle; }
.score-bar { height: 8px; border-radius: 4px; background: #58a6ff; }
footer {
    border-top: 1px solid #30363d;
    padding: 1rem 2rem;
    text-align: center;
    color: #8b949e;
    font-size: 0.8rem;
    margin-top: 3rem;
}
footer a { color: #58a6ff; }
.breadcrumb { color: #8b949e; font-size: 0.85rem; margin-bottom: 1rem; }
h2.section-title { font-size: 1.2rem; color: #e6edf3; margin: 2rem 0 1rem; border-bottom: 1px solid #30363d; padding-bottom: 0.5rem; }
.history-chart { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
.history-chart canvas { width: 100%; max-height: 200px; }
.detail-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 0.75rem; margin: 1rem 0; }
.detail-item { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 0.75rem; }
.detail-item .key { color: #8b949e; font-size: 0.75rem; }
.detail-item .val { color: #58a6ff; font-weight: bold; font-size: 1.1rem; }
"""

_NAV = """<header>
  <h1><a href="{base_url}" style="color:#58a6ff;text-decoration:none;">🤖 agentkit</a></h1>
  <nav>
    <a href="{base_url}">Home</a>
    {topic_links}
    <a href="https://github.com/mikiships/agentkit-cli" target="_blank">GitHub</a>
  </nav>
</header>"""

_FOOTER = """<footer>
  <p>Generated by <a href="https://github.com/mikiships/agentkit-cli">agentkit-cli</a> · {ts}</p>
</footer>"""

_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical_url}">
<script type="application/ld+json">{json_ld}</script>
<style>
{css}
</style>
</head>
<body>
{nav}
{body}
{footer}
</body>
</html>"""


# ---------------------------------------------------------------------------
# SiteEngine
# ---------------------------------------------------------------------------


class SiteEngine:
    """Generate a multi-page static site from agentkit history data."""

    def __init__(
        self,
        config: Optional[SiteConfig] = None,
        db: Optional[HistoryDB] = None,
        db_path: Optional[Path] = None,
    ) -> None:
        self.config = config or SiteConfig()
        self._db = db or HistoryDB(db_path=db_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_site(
        self,
        output_dir: Path,
        topics: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> SiteResult:
        """Generate all pages and write to output_dir."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if topics is not None:
            self.config.topics = topics
        if limit is not None:
            self.config.limit = limit

        pages: List[SitePage] = []

        # Index
        index_page = self.generate_index()
        pages.append(index_page)
        (output_dir / "index.html").write_text(index_page.html, encoding="utf-8")

        # Topic pages
        for topic in self.config.topics:
            tp = self.generate_topic_page(topic)
            pages.append(tp)
            topic_dir = output_dir / "topic"
            topic_dir.mkdir(exist_ok=True)
            (topic_dir / f"{topic}.html").write_text(tp.html, encoding="utf-8")

        # Repo pages
        repo_entries = self._get_all_repos(limit=self.config.limit * len(self.config.topics))
        seen: set = set()
        for entry in repo_entries:
            if entry.repo in seen:
                continue
            seen.add(entry.repo)
            parts = entry.repo.split("/", 1)
            if len(parts) != 2:
                continue
            owner, repo = parts
            rp = self.generate_repo_page(owner, repo)
            pages.append(rp)
            repo_dir = output_dir / "repo" / owner
            repo_dir.mkdir(parents=True, exist_ok=True)
            (repo_dir / f"{repo}.html").write_text(rp.html, encoding="utf-8")

        # Sitemap
        sitemap = self.generate_sitemap(pages)
        (output_dir / "sitemap.xml").write_text(sitemap, encoding="utf-8")

        return SiteResult(pages=pages, sitemap_xml=sitemap)

    def generate_index(self) -> SitePage:
        """Generate index.html."""
        all_repos = self._get_all_repos(limit=self.config.limit)
        total_repos = self._count_unique_repos()
        top_score = max((r.score for r in all_repos), default=0.0)
        latest_ts = max((r.last_run for r in all_repos), default="")

        stats_html = f"""
        <div class="stats">
          <div class="stat-card"><div class="value">{total_repos}</div><div class="label">Repos Scored</div></div>
          <div class="stat-card"><div class="value">{top_score:.0f}</div><div class="label">Top Score</div></div>
          <div class="stat-card"><div class="value">{len(self.config.topics)}</div><div class="label">Topics</div></div>
          <div class="stat-card"><div class="value">{latest_ts[:10] or "—"}</div><div class="label">Last Run</div></div>
        </div>"""

        topics_html = '<div class="topics-grid">' + "".join(
            f'<a class="topic-card" href="{self.config.base_url}topic/{t}.html" style="text-decoration:none;">'
            f'<h3>{t.capitalize()}</h3>'
            f'<p>View rankings</p></a>'
            for t in self.config.topics
        ) + '</div>'

        rows_html = "".join(
            f"<tr>"
            f'<td><a href="{self.config.base_url}repo/{r.repo}.html">{r.repo}</a></td>'
            f"<td>{r.score:.0f}</td>"
            f'<td><span class="badge badge-{r.grade}">{r.grade}</span></td>'
            f"<td>{r.last_run[:10]}</td>"
            f"</tr>"
            for r in all_repos[:20]
        )

        table_html = f"""<h2 class="section-title">Recent Scores</h2>
        <table>
          <thead><tr><th>Repository</th><th>Score</th><th>Grade</th><th>Last Run</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""" if all_repos else "<p style='color:#8b949e'>No scored repos yet. Run <code>agentkit analyze</code> to get started.</p>"

        body = f"""
        <div class="hero">
          <h2>Agent Quality Rankings</h2>
          <p>SEO-optimized rankings of GitHub repos by AI agent-readiness score.</p>
          {stats_html}
        </div>
        <div class="container">
          <h2 class="section-title">Browse by Topic</h2>
          {topics_html}
          {table_html}
        </div>"""

        meta = PageMeta(
            title="agentkit — Agent Quality Rankings",
            description="Browse GitHub repos ranked by AI agent-readiness score across Python, TypeScript, Rust, Go and more.",
            canonical_url=self.config.base_url,
            last_modified=datetime.now(timezone.utc).isoformat()[:10],
        )
        json_ld = json.dumps({
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": meta.title,
            "description": meta.description,
            "url": meta.canonical_url,
        })
        html = self._render_page(body, meta, json_ld)
        return SitePage(path="index.html", html=html, meta=meta)

    def generate_topic_page(self, topic: str) -> SitePage:
        """Generate topic/{topic}.html."""
        repos = self._get_repos_for_topic(topic, limit=self.config.limit)

        rows_html = "".join(
            f"<tr>"
            f"<td>{i+1}</td>"
            f'<td><a href="{self.config.base_url}repo/{r.repo}.html">{r.repo}</a></td>'
            f"<td>{r.score:.0f} "
            f'<span class="score-bar-wrap"><span class="score-bar" style="width:{min(100,r.score):.0f}%"></span></span></td>'
            f'<td><span class="badge badge-{r.grade}">{r.grade}</span></td>'
            f"<td>{r.last_run[:10]}</td>"
            f"</tr>"
            for i, r in enumerate(repos)
        )

        table_html = f"""<table>
          <thead><tr><th>#</th><th>Repository</th><th>Score</th><th>Grade</th><th>Last Run</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""" if repos else "<p style='color:#8b949e'>No repos found for this topic yet.</p>"

        canonical = f"{self.config.base_url}topic/{topic}.html"
        body = f"""
        <div class="container">
          <div class="breadcrumb"><a href="{self.config.base_url}">Home</a> / {topic.capitalize()}</div>
          <h2 class="section-title">{topic.capitalize()} — Agent Quality Rankings</h2>
          <p style="color:#8b949e;margin-bottom:1rem">Top {len(repos)} repos ranked by AI agent-readiness score.</p>
          {table_html}
        </div>"""

        meta = PageMeta(
            title=f"{topic.capitalize()} Repos — Agent Quality Rankings | agentkit",
            description=f"Top {topic} GitHub repos ranked by AI agent-readiness score. Updated automatically.",
            canonical_url=canonical,
            last_modified=datetime.now(timezone.utc).isoformat()[:10],
        )
        json_ld = json.dumps({
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": meta.title,
            "description": meta.description,
            "url": canonical,
        })
        html = self._render_page(body, meta, json_ld)
        return SitePage(path=f"topic/{topic}.html", html=html, meta=meta)

    def generate_repo_page(self, owner: str, repo: str) -> SitePage:
        """Generate repo/{owner}/{repo}.html."""
        full_name = f"{owner}/{repo}"
        rows = self._db.get_history(project=full_name)
        history_scores = [r.get("score", 0) for r in rows]
        latest = rows[0] if rows else {}
        score = latest.get("score", 0.0)
        grade = score_to_grade(score)
        last_run = latest.get("timestamp", "")
        details = {}
        if latest.get("details"):
            try:
                details = json.loads(latest["details"]) if isinstance(latest["details"], str) else latest["details"]
            except Exception:
                pass

        detail_items = "".join(
            f'<div class="detail-item"><div class="key">{k}</div><div class="val">{v}</div></div>'
            for k, v in list(details.items())[:8]
            if isinstance(v, (int, float, str))
        )
        detail_html = f'<div class="detail-grid">{detail_items}</div>' if detail_items else ""

        # Simple SVG history chart
        chart_html = ""
        if len(history_scores) >= 2:
            points = _make_sparkline(history_scores)
            chart_html = f"""<div class="history-chart">
              <p style="color:#8b949e;font-size:0.8rem;margin-bottom:0.5rem">Score history ({len(history_scores)} runs)</p>
              <svg viewBox="0 0 300 80" style="width:100%;height:80px">
                <polyline points="{points}" fill="none" stroke="#58a6ff" stroke-width="2"/>
              </svg>
            </div>"""

        canonical = f"{self.config.base_url}repo/{full_name}.html"
        badge_cls = f"badge-{grade}"
        body = f"""
        <div class="container">
          <div class="breadcrumb"><a href="{self.config.base_url}">Home</a> / <a href="{self.config.base_url}repo/{owner}/">{owner}</a> / {repo}</div>
          <h2 class="section-title">{full_name}</h2>
          <div class="stats" style="justify-content:flex-start">
            <div class="stat-card"><div class="value">{score:.0f}</div><div class="label">Score</div></div>
            <div class="stat-card"><div class="value"><span class="badge {badge_cls}">{grade}</span></div><div class="label">Grade</div></div>
            <div class="stat-card"><div class="value">{len(rows)}</div><div class="label">Runs</div></div>
            <div class="stat-card"><div class="value">{last_run[:10] or "—"}</div><div class="label">Last Run</div></div>
          </div>
          {chart_html}
          {detail_html}
          <p style="margin-top:1.5rem">
            <a href="https://github.com/{full_name}" target="_blank">View on GitHub →</a>
          </p>
        </div>"""

        meta = PageMeta(
            title=f"{full_name} — Agent Quality Score | agentkit",
            description=f"{full_name} scored {score:.0f}/100 (grade {grade}) for AI agent-readiness. Full score breakdown.",
            canonical_url=canonical,
            last_modified=last_run[:10] or datetime.now(timezone.utc).isoformat()[:10],
        )
        json_ld = json.dumps({
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": full_name,
            "description": meta.description,
            "url": f"https://github.com/{full_name}",
            "applicationCategory": "DeveloperApplication",
        })
        html = self._render_page(body, meta, json_ld)
        return SitePage(path=f"repo/{full_name}.html", html=html, meta=meta)

    def generate_sitemap(self, pages: Optional[List[SitePage]] = None) -> str:
        """Generate sitemap.xml for all pages."""
        if pages is None:
            pages = []
        today = datetime.now(timezone.utc).isoformat()[:10]
        entries = "\n".join(
            f"  <url>\n    <loc>{self.config.base_url}{p.path}</loc>\n    <lastmod>{p.meta.last_modified or today}</lastmod>\n  </url>"
            for p in pages
        )
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>"""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_all_repos(self, limit: int = 20) -> List[RepoEntry]:
        rows = self._db.get_history(limit=limit * 10)
        seen: Dict[str, RepoEntry] = {}
        for row in rows:
            proj = row.get("project", "")
            if not proj or "/" not in proj:
                continue
            if proj in seen:
                continue
            score = float(row.get("score", 0))
            seen[proj] = RepoEntry(
                repo=proj,
                score=score,
                grade=score_to_grade(score),
                last_run=row.get("timestamp", ""),
            )
            if len(seen) >= limit:
                break
        return sorted(seen.values(), key=lambda r: r.score, reverse=True)

    def _get_repos_for_topic(self, topic: str, limit: int = 20) -> List[RepoEntry]:
        """Return repos matching topic (by label or project name pattern)."""
        rows = self._db.get_history(limit=500)
        seen: Dict[str, RepoEntry] = {}
        for row in rows:
            proj = row.get("project", "")
            label = row.get("label", "") or ""
            if not proj or "/" not in proj:
                continue
            # Match by label OR simple heuristic: project name contains topic keyword
            if topic.lower() not in (label + proj).lower():
                continue
            if proj in seen:
                continue
            score = float(row.get("score", 0))
            seen[proj] = RepoEntry(
                repo=proj,
                score=score,
                grade=score_to_grade(score),
                last_run=row.get("timestamp", ""),
            )
            if len(seen) >= limit:
                break
        return sorted(seen.values(), key=lambda r: r.score, reverse=True)

    def _count_unique_repos(self) -> int:
        rows = self._db.get_history(limit=10000)
        return len({r.get("project", "") for r in rows if r.get("project", "") and "/" in r.get("project", "")})

    def _render_page(self, body: str, meta: PageMeta, json_ld: str) -> str:
        topic_links = " ".join(
            f'<a href="{self.config.base_url}topic/{t}.html">{t.capitalize()}</a>'
            for t in self.config.topics
        )
        nav = _NAV.format(base_url=self.config.base_url, topic_links=topic_links)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        footer = _FOOTER.format(ts=ts)
        return _PAGE_TEMPLATE.format(
            title=meta.title,
            description=meta.description,
            canonical_url=meta.canonical_url,
            json_ld=json_ld,
            css=_CSS,
            nav=nav,
            body=body,
            footer=footer,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sparkline(scores: List[float]) -> str:
    """Convert a list of scores to SVG polyline points (300x80 viewBox)."""
    if not scores:
        return ""
    mn, mx = min(scores), max(scores)
    rng = mx - mn or 1.0
    n = len(scores)
    pts = []
    for i, s in enumerate(scores):
        x = round(i / max(n - 1, 1) * 280 + 10, 1)
        y = round(80 - ((s - mn) / rng) * 60 - 10, 1)
        pts.append(f"{x},{y}")
    return " ".join(pts)
