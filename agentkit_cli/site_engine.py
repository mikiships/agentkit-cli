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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #080b0f;
  --surface: #0d1117;
  --surface2: #161b22;
  --border: #21262d;
  --text: #e6edf3;
  --muted: #7d8590;
  --accent: #3fb950;
  --accent-dim: rgba(63,185,80,0.12);
  --blue: #58a6ff;
  --blue-dim: rgba(88,166,255,0.10);
  --mono: 'JetBrains Mono', 'Courier New', monospace;
  --sans: 'Inter', system-ui, sans-serif;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--sans);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

a { color: var(--blue); text-decoration: none; }
a:hover { color: var(--accent); }

/* ── Nav ── */
header {
  position: sticky; top: 0; z-index: 100;
  background: rgba(8,11,15,0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  padding: 0 2rem;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.nav-brand {
  font-family: var(--mono);
  font-size: 1rem;
  font-weight: 500;
  color: var(--accent);
  letter-spacing: -0.02em;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.nav-brand span { color: var(--muted); font-weight: 400; }
header nav { display: flex; align-items: center; gap: 1.5rem; }
header nav a {
  font-size: 0.85rem;
  color: var(--muted);
  transition: color 0.15s;
}
header nav a:hover { color: var(--text); }
.nav-cta {
  font-size: 0.8rem !important;
  color: var(--accent) !important;
  border: 1px solid rgba(63,185,80,0.4);
  padding: 0.3rem 0.75rem;
  border-radius: 6px;
  transition: background 0.15s !important;
}
.nav-cta:hover { background: var(--accent-dim) !important; }

/* ── Hero ── */
.hero {
  padding: 7rem 2rem 5rem;
  text-align: center;
  position: relative;
  overflow: hidden;
}
.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 80% 60% at 50% 0%, rgba(63,185,80,0.07) 0%, transparent 70%);
  pointer-events: none;
}
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-family: var(--mono);
  font-size: 0.75rem;
  color: var(--accent);
  background: var(--accent-dim);
  border: 1px solid rgba(63,185,80,0.3);
  padding: 0.3rem 0.8rem;
  border-radius: 100px;
  margin-bottom: 2rem;
  opacity: 0;
  animation: fadeUp 0.6s ease 0.1s forwards;
}
.hero h1 {
  font-size: clamp(2.5rem, 6vw, 4rem);
  font-weight: 700;
  letter-spacing: -0.04em;
  line-height: 1.1;
  margin-bottom: 1.25rem;
  opacity: 0;
  animation: fadeUp 0.6s ease 0.2s forwards;
}
.hero h1 em {
  font-style: normal;
  color: var(--accent);
}
.hero-sub {
  font-size: 1.1rem;
  color: var(--muted);
  max-width: 480px;
  margin: 0 auto 2.5rem;
  line-height: 1.6;
  opacity: 0;
  animation: fadeUp 0.6s ease 0.3s forwards;
}
.hero-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
  opacity: 0;
  animation: fadeUp 0.6s ease 0.4s forwards;
}
.install-block {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.6rem 1rem;
  font-family: var(--mono);
  font-size: 0.9rem;
  color: var(--text);
}
.install-block .prompt { color: var(--accent); }
.btn-gh {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.6rem 1.1rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.85rem;
  transition: border-color 0.15s, color 0.15s;
}
.btn-gh:hover { border-color: var(--blue); color: var(--blue); }

/* ── Stats strip ── */
.stats-strip {
  display: flex;
  justify-content: center;
  gap: 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}
.stat-item {
  flex: 1;
  max-width: 200px;
  padding: 1.75rem 1rem;
  text-align: center;
  border-right: 1px solid var(--border);
}
.stat-item:last-child { border-right: none; }
.stat-num {
  font-family: var(--mono);
  font-size: 1.9rem;
  font-weight: 600;
  color: var(--accent);
  line-height: 1;
  margin-bottom: 0.35rem;
}
.stat-label { font-size: 0.78rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }

/* ── Container ── */
.container { max-width: 920px; margin: 0 auto; padding: 3rem 1.5rem; }

/* ── Section titles ── */
.section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}
h2.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.section-note { font-size: 0.8rem; color: var(--muted); }

/* ── Ecosystem pills ── */
.ecosystem-pills {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 2rem;
}
.pill {
  font-size: 0.8rem;
  padding: 0.3rem 0.85rem;
  border-radius: 100px;
  border: 1px solid var(--border);
  color: var(--muted);
  cursor: pointer;
  transition: all 0.15s;
  text-decoration: none;
}
.pill:hover, .pill.active { border-color: var(--accent); color: var(--accent); background: var(--accent-dim); }

/* ── Table ── */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}
thead tr { border-bottom: 1px solid var(--border); }
th {
  padding: 0.5rem 0.75rem;
  color: var(--muted);
  font-weight: 500;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  text-align: left;
}
td {
  padding: 0.75rem 0.75rem;
  border-bottom: 1px solid rgba(33,38,45,0.6);
  vertical-align: middle;
}
tbody tr {
  opacity: 0;
  transform: translateY(6px);
  transition: background 0.15s;
}
tbody tr.visible {
  opacity: 1;
  transform: none;
  transition: opacity 0.3s ease, transform 0.3s ease, background 0.15s;
}
tbody tr:hover { background: var(--surface2); }
.repo-name { font-family: var(--mono); font-size: 0.85rem; font-weight: 500; }
.repo-name a { color: var(--text); }
.repo-name a:hover { color: var(--accent); }

/* ── Score bar ── */
.score-cell { display: flex; align-items: center; gap: 0.6rem; }
.score-val { font-family: var(--mono); font-size: 0.85rem; min-width: 2.2rem; }
.score-bar-wrap {
  flex: 1; max-width: 80px;
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  overflow: hidden;
}
.score-bar {
  height: 100%;
  border-radius: 2px;
  background: var(--accent);
  width: 0;
  transition: width 0.6s ease;
}

/* ── Grade badge ── */
.badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 5px;
  font-family: var(--mono);
  font-weight: 600;
  font-size: 0.78rem;
}
.badge-A { background: rgba(26,127,55,0.25); color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }
.badge-B { background: rgba(88,166,255,0.15); color: #58a6ff; border: 1px solid rgba(88,166,255,0.3); }
.badge-C { background: rgba(210,153,34,0.15); color: #d29922; border: 1px solid rgba(210,153,34,0.3); }
.badge-D { background: rgba(248,81,73,0.12); color: #f85149; border: 1px solid rgba(248,81,73,0.25); }
.badge-F { background: rgba(248,81,73,0.12); color: #f85149; border: 1px solid rgba(248,81,73,0.25); }

/* ── Topic page cards (cardless: sections instead) ── */
.topics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  margin: 2rem 0;
}
.topic-block {
  background: var(--surface);
  padding: 1.5rem;
  transition: background 0.15s;
}
.topic-block:hover { background: var(--surface2); }
.topic-block h3 {
  font-family: var(--mono);
  font-size: 0.9rem;
  color: var(--accent);
  margin-bottom: 0.35rem;
}
.topic-block p { font-size: 0.8rem; color: var(--muted); }

/* ── Repo detail ── */
.breadcrumb { font-size: 0.82rem; color: var(--muted); margin-bottom: 1.5rem; }
.breadcrumb a { color: var(--muted); }
.breadcrumb a:hover { color: var(--text); }
.repo-hero { margin-bottom: 2.5rem; }
.repo-hero h2 { font-family: var(--mono); font-size: 1.5rem; font-weight: 600; margin-bottom: 0.5rem; }
.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  margin: 1.25rem 0;
}
.detail-item { background: var(--surface); padding: 1rem; }
.detail-item .key { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.3rem; }
.detail-item .val { font-family: var(--mono); font-size: 1.1rem; font-weight: 600; color: var(--accent); }
.history-chart { background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; margin: 1.5rem 0; }

/* ── Footer ── */
footer {
  border-top: 1px solid var(--border);
  padding: 1.5rem 2rem;
  text-align: center;
  color: var(--muted);
  font-size: 0.78rem;
}
footer a { color: var(--muted); }
footer a:hover { color: var(--text); }

/* ── Animations ── */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
"""

_NAV = """<header>
  <div class="nav-brand">agentkit<span>/cli</span></div>
  <nav>
    <a href="{base_url}">Home</a>
    {topic_links}
    <a href="https://github.com/mikiships/agentkit-cli" target="_blank" class="nav-cta">GitHub ↗</a>
  </nav>
</header>"""

_FOOTER = """<footer>
  <p>Built with <a href="https://github.com/mikiships/agentkit-cli">agentkit-cli</a> · {ts} · <a href="https://pypi.org/project/agentkit-cli/">PyPI</a></p>
</footer>"""

_SCROLL_JS = """<script>
// Stagger table rows in on scroll
(function() {
  var rows = document.querySelectorAll('tbody tr');
  if (!rows.length) return;
  var io = new IntersectionObserver(function(entries) {
    entries.forEach(function(e) {
      if (e.isIntersecting) {
        var delay = Array.from(rows).indexOf(e.target) * 40;
        setTimeout(function() { e.target.classList.add('visible'); }, delay);
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.05 });
  rows.forEach(function(r) { io.observe(r); });

  // Animate score bars
  var bars = document.querySelectorAll('.score-bar[data-pct]');
  var bioS = new IntersectionObserver(function(entries) {
    entries.forEach(function(e) {
      if (e.isIntersecting) {
        e.target.style.width = e.target.getAttribute('data-pct') + '%';
        bioS.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });
  bars.forEach(function(b) { bioS.observe(b); });
})();
</script>"""

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
{scroll_js}
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
            repo_dir = output_dir / "repo"
            repo_dir.mkdir(parents=True, exist_ok=True)
            (repo_dir / f"{_safe_name(entry.repo)}.html").write_text(rp.html, encoding="utf-8")

        # Sitemap
        sitemap = self.generate_sitemap(pages)
        (output_dir / "sitemap.xml").write_text(sitemap, encoding="utf-8")

        return SiteResult(pages=pages, sitemap_xml=sitemap)

    def generate_index(self) -> SitePage:
        """Generate index.html."""
        all_repos = self._get_all_repos(limit=self.config.limit)
        total_repos = self._count_unique_repos()
        top_score = max((r.score for r in all_repos), default=0.0)
        rows_html = "".join(
            f"<tr>"
            f'<td class="repo-name"><a href="{self.config.base_url}repo/{_safe_name(r.repo)}.html">{r.repo}</a></td>'
            f'<td><div class="score-cell"><span class="score-val">{r.score:.0f}</span>'
            f'<span class="score-bar-wrap"><span class="score-bar" data-pct="{min(100,r.score):.0f}"></span></span></div></td>'
            f'<td><span class="badge badge-{r.grade}">{r.grade}</span></td>'
            f"</tr>"
            for r in all_repos[:20]
        )

        table_html = f"""
        <div class="section-header">
          <h2 class="section-title">Rankings</h2>
          <span class="section-note">{total_repos} repos scored</span>
        </div>
        <table>
          <thead><tr><th>Repository</th><th>Score</th><th>Grade</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""" if all_repos else "<p style='color:var(--muted)'>No scored repos yet. Run <code>agentkit quickstart</code> to get started.</p>"

        topics_pills = "".join(
            f'<a class="pill" href="{self.config.base_url}topic/{t}.html">{t.capitalize()}</a>'
            for t in self.config.topics
        )

        body = f"""
        <div class="hero">
          <div class="hero-badge">v0.84 &middot; {total_repos} repos scored</div>
          <h1>Is your repo ready<br>for <em>AI agents</em>?</h1>
          <p class="hero-sub">agentkit scores GitHub repos for AI-agent readiness. Lint rules, context files, test coverage, CI patterns. One number.</p>
          <div class="hero-actions">
            <div class="install-block"><span class="prompt">$</span> pip install agentkit-cli</div>
            <a href="https://github.com/mikiships/agentkit-cli" target="_blank" class="btn-gh">View on GitHub</a>
          </div>
        </div>

        <div class="stats-strip">
          <div class="stat-item"><div class="stat-num">{total_repos}</div><div class="stat-label">Repos</div></div>
          <div class="stat-item"><div class="stat-num">{top_score:.0f}</div><div class="stat-label">Top Score</div></div>
          <div class="stat-item"><div class="stat-num">{len(self.config.topics)}</div><div class="stat-label">Ecosystems</div></div>
        </div>

        <div class="container">
          <div class="ecosystem-pills">{topics_pills}</div>
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
            f'<td class="repo-name"><a href="{self.config.base_url}repo/{_safe_name(r.repo)}.html">{r.repo}</a></td>'
            f'<td><div class="score-cell"><span class="score-val">{r.score:.0f}</span>'
            f'<span class="score-bar-wrap"><span class="score-bar" data-pct="{min(100,r.score):.0f}"></span></span></div></td>'
            f'<td><span class="badge badge-{r.grade}">{r.grade}</span></td>'
            f"</tr>"
            for i, r in enumerate(repos)
        )

        table_html = f"""<table>
          <thead><tr><th>#</th><th>Repository</th><th>Score</th><th>Grade</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""" if repos else "<p style='color:var(--muted)'>No repos found for this topic yet.</p>"

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

        canonical = f"{self.config.base_url}repo/{_safe_name(full_name)}.html"
        badge_cls = f"badge-{grade}"
        body = f"""
        <div class="container">
          <div class="breadcrumb"><a href="{self.config.base_url}">Home</a> / {full_name}</div>
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
        return SitePage(path=f"repo/{_safe_name(full_name)}.html", html=html, meta=meta)

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
            scroll_js=_SCROLL_JS,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_name(s: str) -> str:
    """Sanitize a string for use as a filesystem path segment.

    Replaces characters that are invalid or problematic on common filesystems:
      ':' -> '-'  (colons, e.g. from 'github:owner')
      '/' -> '--' (slashes inside identifiers, not path separators)
    """
    return s.replace(":", "-").replace("/", "--")


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
