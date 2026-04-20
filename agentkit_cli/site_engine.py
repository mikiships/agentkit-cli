"""agentkit site_engine — multi-page static site generator from history DB."""
from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from agentkit_cli.history import HistoryDB
from agentkit_cli.user_scorecard import score_to_grade

try:
    from agentkit_cli import __version__ as _PKG_VERSION
except Exception:
    _PKG_VERSION = "0.86"

_FRONTDOOR_VERSION = "1.2.0"
_FRONTDOOR_TEST_COUNT = 4824
_FRONTDOOR_VERSION_COUNT = 111
_FRONTDOOR_PACKAGE_COUNT = 6
_REPO_ROOT = Path(__file__).resolve().parent.parent


def _git_output(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            stderr=subprocess.DEVNULL,
            text=True,
            cwd=_REPO_ROOT,
        ).strip()
    except Exception:
        return ""


def _latest_release_version() -> str:
    tag = _git_output("tag", "--list", "v[0-9]*.[0-9]*.[0-9]*", "--sort=-version:refname").splitlines()[:1]
    if tag and tag[0].startswith("v"):
        return tag[0][1:]
    return _FRONTDOOR_VERSION


def _released_test_count(version: str) -> int:
    tag = f"v{version}"
    for path in ("BUILD-REPORT.md", f"BUILD-REPORT-v{version}.md"):
        content = _git_output("show", f"{tag}:{path}")
        if not content:
            continue
        for pattern in (
            r"final full suite: .*?-> `([0-9]+) passed",
            r"-> `([0-9]+) passed,",
            r"`([0-9]+) passed",
        ):
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return int(match.group(1))
    return _FRONTDOOR_TEST_COUNT


def _released_frontdoor_defaults() -> dict[str, int | str]:
    version = _latest_release_version()
    return {
        "version": version,
        "tests": _released_test_count(version),
        "versions": _version_stat_from_version(version),
        "packages": _FRONTDOOR_PACKAGE_COUNT,
    }


def build_frontdoor_stats(
    existing: Optional[dict[str, Any]] = None,
    *,
    version: Optional[str] = None,
    tests: Optional[int] = None,
    versions: Optional[int] = None,
    packages: Optional[int] = None,
    refreshed_at: Optional[str] = None,
    prefer_existing: bool = True,
) -> dict[str, Any]:
    """Build the canonical front-door stats payload shared by data.json and index.html."""
    existing = existing or {}
    released = _released_frontdoor_defaults()
    resolved_version = version or (existing.get("version") if prefer_existing else None) or str(released["version"])
    resolved_tests = tests if tests is not None else (existing.get("tests") if prefer_existing else None) or int(released["tests"])
    inferred_versions = _version_stat_from_version(str(resolved_version))
    resolved_versions = versions if versions is not None else (existing.get("versions") if prefer_existing else None) or inferred_versions
    resolved_packages = packages if packages is not None else (existing.get("packages") if prefer_existing else None) or int(released["packages"])
    return {
        "version": str(resolved_version),
        "tests": int(resolved_tests),
        "versions": int(resolved_versions),
        "packages": int(resolved_packages),
        "refreshed_at": refreshed_at or existing.get("refreshed_at") or datetime.now(timezone.utc).isoformat(),
    }


def _version_stat_from_version(version: str) -> int:
    match = re.search(r"(\d+)\.(\d+)", version or "")
    if not match:
        return _FRONTDOOR_VERSION_COUNT
    major = int(match.group(1))
    minor = int(match.group(2))
    return major * 100 + minor

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
  padding: 7rem 2rem 4.5rem;
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
  font-size: clamp(2.7rem, 6vw, 4.4rem);
  font-weight: 700;
  letter-spacing: -0.04em;
  line-height: 1.05;
  margin-bottom: 1rem;
  opacity: 0;
  animation: fadeUp 0.6s ease 0.2s forwards;
}
.hero h1 em {
  font-style: normal;
  color: var(--accent);
}
.hero-sub {
  font-size: 1.08rem;
  color: var(--muted);
  max-width: 760px;
  margin: 0 auto 2rem;
  line-height: 1.7;
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
  padding: 0.7rem 1rem;
  font-family: var(--mono);
  font-size: 0.9rem;
  color: var(--text);
}
.install-block .prompt { color: var(--accent); }
.btn-gh {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  padding: 0.7rem 1.1rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.85rem;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}
.btn-gh:hover { border-color: var(--blue); color: var(--blue); background: var(--blue-dim); }
.hero-proof {
  max-width: 920px;
  margin: 2.5rem auto 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
  opacity: 0;
  animation: fadeUp 0.6s ease 0.5s forwards;
}
.proof-item {
  background: var(--surface);
  padding: 1.25rem;
  text-align: left;
}
.proof-kicker {
  display: block;
  color: var(--accent);
  font-family: var(--mono);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 0.5rem;
}
.proof-item strong {
  display: block;
  font-size: 1rem;
  margin-bottom: 0.45rem;
}
.proof-item p {
  color: var(--muted);
  font-size: 0.9rem;
  line-height: 1.6;
}

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
.stat-num, .stat-value {
  font-family: var(--mono);
  font-size: 1.9rem;
  font-weight: 600;
  color: var(--accent);
  line-height: 1;
  margin-bottom: 0.35rem;
}
.stat-label { font-size: 0.78rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
.source-badge { display: inline-block; font-size: 0.65rem; padding: 0.1rem 0.4rem; border-radius: 3px; margin-left: 0.3rem; }
.source-ecosystem { background: rgba(63,185,80,0.15); color: var(--accent); }
.source-community { background: rgba(88,166,255,0.15); color: var(--blue); }
.source-manual { background: rgba(230,180,90,0.15); color: #e6b45a; }

/* ── Container ── */
.container { max-width: 1080px; margin: 0 auto; padding: 3.25rem 1.5rem; }

/* ── Section titles ── */
.section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
}
h2.section-title {
  font-size: 0.96rem;
  font-weight: 600;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.section-note { font-size: 0.9rem; color: var(--muted); line-height: 1.6; max-width: 720px; }
.section-lead {
  color: var(--muted);
  font-size: 1rem;
  line-height: 1.7;
  max-width: 760px;
  margin: 0.75rem 0 0;
}
.section-frame {
  background: linear-gradient(180deg, rgba(13,17,23,0.98), rgba(13,17,23,0.9));
  border: 1px solid var(--border);
  border-radius: 16px;
}

.workflow-grid, .feature-grid, .trust-grid, .secondary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}
.feature-grid { margin-top: 1.5rem; }
.feature-card, .workflow-card, .trust-card, .secondary-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.25rem;
}
.workflow-card .step {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 999px;
  background: var(--accent-dim);
  border: 1px solid rgba(63,185,80,0.3);
  color: var(--accent);
  font-family: var(--mono);
  font-size: 0.8rem;
  margin-bottom: 0.9rem;
}
.workflow-card h3, .feature-card h3, .trust-card h3, .secondary-card h3 {
  font-size: 1rem;
  margin-bottom: 0.55rem;
}
.workflow-card p, .feature-card p, .trust-card p, .secondary-card p {
  color: var(--muted);
  font-size: 0.92rem;
  line-height: 1.7;
}
.feature-card code, .secondary-card code {
  font-family: var(--mono);
  font-size: 0.82rem;
}
.secondary-card pre { margin-top: 0.9rem; }

.quickstart-shell {
  margin-top: 1.5rem;
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
  gap: 1rem;
}
.code-block {
  background: #05080c;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.15rem 1.2rem;
  overflow-x: auto;
}
.code-block code {
  font-family: var(--mono);
  font-size: 0.88rem;
  line-height: 1.8;
  color: var(--text);
  white-space: pre;
}
.quickstart-notes {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.25rem;
}
.quickstart-list {
  list-style: none;
  display: grid;
  gap: 0.8rem;
  margin: 1rem 0 1.25rem;
}
.quickstart-list li {
  color: var(--muted);
  line-height: 1.65;
  padding-left: 1.4rem;
  position: relative;
}
.quickstart-list li::before {
  content: '•';
  color: var(--accent);
  position: absolute;
  left: 0;
}
.inline-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1rem;
}

.recently-scored-list .repo-list {
  list-style: none;
  display: grid;
  gap: 0.75rem;
}
.repo-item {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) auto auto auto auto;
  gap: 0.65rem;
  align-items: center;
  padding: 0.9rem 1rem;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface);
}
.eco-badge, .grade {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 3.5rem;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-family: var(--mono);
  border: 1px solid var(--border);
  color: var(--muted);
}
.data-ts, .loading-msg {
  color: var(--muted);
  font-size: 0.82rem;
  margin-top: 0.9rem;
}

/* ── Ecosystem pills ── */
.ecosystem-pills {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
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
.badge-A, .grade-a { background: rgba(26,127,55,0.25); color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }
.badge-B, .grade-b { background: rgba(88,166,255,0.15); color: #58a6ff; border: 1px solid rgba(88,166,255,0.3); }
.badge-C, .grade-c { background: rgba(210,153,34,0.15); color: #d29922; border: 1px solid rgba(210,153,34,0.3); }
.badge-D, .grade-d { background: rgba(248,81,73,0.12); color: #f85149; border: 1px solid rgba(248,81,73,0.25); }
.badge-F, .grade-f { background: rgba(248,81,73,0.12); color: #f85149; border: 1px solid rgba(248,81,73,0.25); }

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

@media (max-width: 900px) {
  .hero-proof, .workflow-grid, .feature-grid, .trust-grid, .secondary-grid, .quickstart-shell {
    grid-template-columns: 1fr;
  }
  .stats-strip {
    flex-wrap: wrap;
  }
  .stat-item {
    min-width: 33.33%;
    max-width: none;
  }
  .repo-item {
    grid-template-columns: 1fr 1fr;
    align-items: start;
  }
}

@media (max-width: 640px) {
  header {
    height: auto;
    align-items: flex-start;
    flex-direction: column;
    gap: 0.8rem;
    padding: 1rem 1.25rem;
  }
  header nav {
    flex-wrap: wrap;
    gap: 0.9rem;
  }
  .hero {
    padding-left: 1.25rem;
    padding-right: 1.25rem;
  }
  .hero h1 {
    font-size: clamp(2.2rem, 10vw, 3.2rem);
  }
  .hero-actions {
    flex-direction: column;
  }
  .install-block, .btn-gh, .nav-cta {
    width: 100%;
    justify-content: center;
  }
  .stat-item {
    min-width: 50%;
  }
  .section-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .repo-item {
    grid-template-columns: 1fr;
  }
}

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
    <a href="{base_url}#quickstart">Quickstart</a>
    <a href="{base_url}#proof">Proof</a>
    <a href="{base_url}#rankings">Rankings</a>
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

// Dynamic leaderboard data from data.json
function gradeClass(g) { return 'grade-' + (g || 'c').toLowerCase(); }
function renderRecentlyScored(data) {
  var el = document.getElementById('recently-scored-list');
  if (!el) return;
  var top = data.repos ? data.repos.slice(0, 5) : [];
  var html = '<ul class="repo-list">';
  top.forEach(function(r) {
    var src = r.source || 'ecosystem';
    var srcLabel = src === 'community' ? 'community' : src === 'manual' ? 'manual' : 'ecosystem';
    var srcClass = 'source-' + srcLabel;
    html += '<li class="repo-item">'
      + '<a href="' + (r.url || '#') + '" target="_blank" rel="noopener" class="repo-name">' + (r.name || '') + '</a>'
      + '<span class="eco-badge">' + (r.ecosystem || '') + '</span>'
      + '<span class="source-badge ' + srcClass + '">' + srcLabel + '</span>'
      + '<span class="score-val">' + (r.score || 0) + '</span>'
      + '<span class="grade ' + gradeClass(r.grade) + '">' + (r.grade || '') + '</span>'
      + '</li>';
  });
  html += '</ul>';
  el.innerHTML = html;
  var statEl = document.getElementById('repos-scored-stat');
  if (statEl && data.stats && data.stats.total) { statEl.textContent = data.stats.total; }
  var communityCount = (data.repos || []).filter(function(r) { return r.source === 'community'; }).length;
  var commEl = document.getElementById('community-scored-stat');
  if (commEl) { commEl.textContent = communityCount; }
}
fetch('/agentkit-cli/data.json')
  .then(function(r) { return r.ok ? r.json() : Promise.reject(r.status); })
  .then(renderRecentlyScored)
  .catch(function() {
    var el = document.getElementById('recently-scored-list');
    if (el) el.innerHTML = '<p style="color:var(--muted)">Score data unavailable.</p>';
  });
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

    def generate_index(self, site_data: Optional[dict] = None) -> SitePage:
        """Generate index.html."""
        frontdoor = build_frontdoor_stats((site_data or {}).get("frontdoor"))
        if site_data and site_data.get("repos") is not None:
            all_repos = [
                RepoEntry(
                    repo=repo.get("name", ""),
                    score=float(repo.get("score", 0)),
                    grade=repo.get("grade", score_to_grade(float(repo.get("score", 0)))),
                    last_run=repo.get("synced_at", ""),
                    details=repo,
                )
                for repo in site_data.get("repos", [])
                if repo.get("name")
            ]
            total_repos = int((site_data.get("stats") or {}).get("total", len(all_repos)))
            community_repos = sum(1 for repo in site_data.get("repos", []) if repo.get("source") == "community")
        else:
            all_repos = self._get_all_repos(limit=self.config.limit)
            total_repos = self._count_unique_repos()
            community_repos = 0
        rows_html = "".join(
            f"<tr>"
            f'<td class="repo-name"><a href="{self.config.base_url}repo/{_safe_name(r.repo)}.html">{r.repo}</a></td>'
            f'<td><div class="score-cell"><span class="score-val">{r.score:.0f}</span>'
            f'<span class="score-bar-wrap"><span class="score-bar" data-pct="{min(100,r.score):.0f}"></span></span></div></td>'
            f'<td><span class="badge badge-{r.grade}">{r.grade}</span></td>'
            f"</tr>"
            for r in all_repos[:20]
        )

        table_html = f"""<table>
          <thead><tr><th>Repository</th><th>Score</th><th>Grade</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""" if all_repos else "<p style='color:var(--muted)'>No scored repos yet. Run <code>agentkit quickstart</code> to get started.</p>"

        topics_pills = "".join(
            f'<a class="pill" href="{self.config.base_url}topic/{t}.html">{t.capitalize()}</a>'
            for t in self.config.topics
        )

        body = f"""
        <div class="hero">
          <div class="hero-badge">v{frontdoor['version']} &middot; open source workflow kit for AI coding agents</div>
          <h1>Keep <em>one canonical source</em><br>for every AI coding agent</h1>
          <p class="hero-sub">agentkit-cli gives you a source-first workflow for agent context and execution rules. Write once in <code>.agentkit/source.md</code>, project that into AGENTS.md, CLAUDE.md, GEMINI.md, COPILOT.md, AGENT.md, and <code>llms.txt</code>, add an <code>agentkit contract</code> when work needs shared guardrails, then score what ships.</p>
          <div class="hero-actions">
            <div class="install-block"><span class="prompt">$</span> pip install agentkit-cli</div>
            <a href="#quickstart" class="nav-cta">See quickstart ↓</a>
            <a href="https://github.com/mikiships/agentkit-cli" target="_blank" class="btn-gh">View on GitHub</a>
          </div>
          <div class="hero-proof">
            <div class="proof-item">
              <span class="proof-kicker">Source</span>
              <strong>Stop maintaining the same prompt file six times.</strong>
              <p>Keep one source of truth, then project it into the filenames real agents already read.</p>
            </div>
            <div class="proof-item">
              <span class="proof-kicker">Execution</span>
              <strong>Make every agent see the same job contract.</strong>
              <p>Use <code>agentkit contract</code> for scope, deliverables, checks, and team-wide execution rules.</p>
            </div>
            <div class="proof-item">
              <span class="proof-kicker">Guardrails</span>
              <strong>Catch drift before agent runs go sideways.</strong>
              <p>Lint context files, gate quality in CI, and review transcript waste instead of guessing.</p>
            </div>
            <div class="proof-item">
              <span class="proof-kicker">Proof</span>
              <strong>{frontdoor['tests']} tests, {frontdoor['versions']} shipped versions, {frontdoor['packages']} packages.</strong>
              <p>Real release cadence and real surface area, not a one-command demo that stops at the headline.</p>
            </div>
          </div>
        </div>

        <div class="stats-strip" id="proof">
          <div class="stat-item stat-card"><div class="stat-value" data-stat="tests">{frontdoor['tests']}</div><div class="stat-label">Tests</div></div>
          <div class="stat-item stat-card"><div class="stat-value" data-stat="versions">{frontdoor['versions']}</div><div class="stat-label">Versions</div></div>
          <div class="stat-item stat-card"><div class="stat-value" data-stat="packages">{frontdoor['packages']}</div><div class="stat-label">Packages</div></div>
          <div class="stat-item stat-card"><div class="stat-num" id="repos-scored-stat">{total_repos}</div><div class="stat-label">Repos Scored</div></div>
          <div class="stat-item stat-card"><div class="stat-num" id="community-scored-stat">{community_repos}</div><div class="stat-label">Community Scored</div></div>
        </div>

        <section class="workflow-section">
          <div class="container section-frame">
            <div class="section-header">
              <div>
                <h2 class="section-title">How agentkit works</h2>
                <p class="section-lead">The front door is a repo workflow, not just a leaderboard. Start with a canonical source, project it into agent-specific files, and put measurable guardrails around the whole loop.</p>
              </div>
            </div>
            <div class="workflow-grid">
              <div class="workflow-card"><span class="step">01</span><h3>Write the canonical source</h3><p>Initialize <code>.agentkit/source.md</code> so your team edits one file instead of manually keeping AGENTS.md, CLAUDE.md, and friends in sync.</p></div>
              <div class="workflow-card"><span class="step">02</span><h3>Project into real agent files</h3><p>Generate the filenames existing tools expect, so Claude Code, Codex, Gemini, Copilot, and MCP flows inherit the same context.</p></div>
              <div class="workflow-card"><span class="step">03</span><h3>Score, gate, and learn</h3><p>Add contracts, lint for drift, benchmark execution quality, and inspect transcripts so the workflow gets better over time.</p></div>
            </div>
          </div>
        </section>

        <section class="quickstart-section" id="quickstart">
          <div class="container section-frame">
            <div class="section-header">
              <div>
                <h2 class="section-title">Quickstart</h2>
                <p class="section-lead">This is the fastest path to a useful repo setup. You can get a canonical source, write the projected files, add an execution contract, and score the result in a few commands.</p>
              </div>
            </div>
            <div class="quickstart-shell">
              <pre class="code-block"><code>pip install agentkit-cli
agentkit source --init
agentkit project --write
agentkit contract --init
agentkit score</code></pre>
              <div class="quickstart-notes">
                <h3>What those commands do</h3>
                <ul class="quickstart-list">
                  <li><strong><code>source --init</code></strong> creates the canonical source file at <code>.agentkit/source.md</code>.</li>
                  <li><strong><code>project --write</code></strong> fans that source out into the filenames AI tools already read.</li>
                  <li><strong><code>contract --init</code></strong> gives each agent run a shared execution brief with clear constraints.</li>
                  <li><strong><code>score</code></strong> tells you whether the setup is actually ready for agent work.</li>
                </ul>
                <div class="inline-links">
                  <a href="https://pypi.org/project/agentkit-cli/" target="_blank" class="btn-gh">PyPI ↗</a>
                  <a href="https://github.com/mikiships/agentkit-cli" target="_blank" class="btn-gh">Docs and source ↗</a>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="features-section">
          <div class="container">
            <div class="section-header">
              <div>
                <h2 class="section-title">The workflow stack</h2>
                <p class="section-lead">agentkit-cli is the entry point, but the product story is the full workflow around source management, projection, scoring, linting, benchmarking, and transcript learning.</p>
              </div>
            </div>
            <div class="feature-grid">
              <div class="feature-card"><h3>agentkit-cli</h3><p>The orchestration entry point for source, project, contract, score, and guard flows.</p></div>
              <div class="feature-card"><h3>agentmd</h3><p>Generate or tighten agent-facing context files from the canonical source before they drift.</p></div>
              <div class="feature-card"><h3>agentlint</h3><p>Catch stale paths, year-rot, missing references, and bloated instructions before they mislead agents.</p></div>
              <div class="feature-card"><h3>coderace</h3><p>Benchmark AI coding agents on your own tasks instead of trusting generic benchmark marketing.</p></div>
              <div class="feature-card"><h3>agentreflect</h3><p>Read transcript history to see where agent runs burned budget, stalled, or repeated avoidable mistakes.</p></div>
              <div class="feature-card"><h3>agentkit-mcp</h3><p>Expose the toolkit through MCP when you want the same workflow available inside other agent surfaces.</p></div>
            </div>
          </div>
        </section>

        <section class="recently-scored-section" id="recently-scored">
          <div class="container section-frame">
            <div class="section-header">
              <div>
                <h2 class="section-title">Public proof</h2>
                <p class="section-lead">The public site still matters, but it belongs as evidence for the workflow. These scorecards show what the toolkit measures against real repositories.</p>
              </div>
            </div>
            <div id="recently-scored-list" class="recently-scored-list">
              <p class="loading-msg">Loading...</p>
            </div>
          </div>
        </section>

        <section class="commands-section">
          <div class="container">
            <div class="section-header">
              <div>
                <h2 class="section-title">Core commands</h2>
                <p class="section-lead">The high-leverage commands line up with the workflow: source, project, contract, score, analyze, and guard.</p>
              </div>
            </div>
            <table class="cmd-table">
              <thead><tr><th>Command</th><th>Description</th></tr></thead>
              <tbody>
                <tr><td>agentkit source --init</td><td>Create the dedicated canonical source file at <code>.agentkit/source.md</code></td></tr>
                <tr><td>agentkit project --write</td><td>Write AGENTS.md, CLAUDE.md, GEMINI.md, COPILOT.md, AGENT.md, and <code>llms.txt</code> from that source</td></tr>
                <tr><td>agentkit contract --init</td><td>Create an <code>agentkit contract</code> so every agent sees the same scope, deliverables, and validation rules</td></tr>
                <tr><td>agentkit score</td><td>Compute the repo's composite agent-readiness score</td></tr>
                <tr><td>agentkit analyze github:owner/repo --share</td><td>Analyze a public repo and publish a shareable scorecard</td></tr>
                <tr><td>agentkit burn --path ./transcripts</td><td>Inspect local coding-agent transcript spend and waste patterns</td></tr>
                <tr><td>agentkit gate --min-score 80</td><td>Fail CI when the setup drops below your quality bar</td></tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="secondary-section">
          <div class="container secondary-grid">
            <div class="secondary-card">
              <h3>Explore live rankings</h3>
              <p>Browse ecosystem scoreboards and repo pages when you want examples, comparisons, or public proof points.</p>
              <div class="inline-links" style="margin-top:1rem">{topics_pills}<a class="pill" href="leaderboard.html">Leaderboard</a><a class="pill" href="trending.html">Trending</a></div>
            </div>
            <div class="secondary-card" id="org-leaderboard">
              <h3>Org leaderboard</h3>
              <p>Rank all public repos in a GitHub org to spot where agent workflows are already strong and where they need cleanup.</p>
              <pre class="code-block"><code>agentkit org github:ORG</code></pre>
            </div>
            <div class="secondary-card">
              <h3>Share a developer scorecard</h3>
              <p>Generate a public profile card when you want a simple external artifact for a person or repository set.</p>
              <pre class="code-block"><code>agentkit user-scorecard github:USERNAME</code></pre>
            </div>
          </div>
        </section>

        <div class="container" id="rankings">
          <div class="section-header">
            <div>
              <h2 class="section-title">Recent rankings</h2>
              <p class="section-lead">A sample of currently scored repositories. The rankings are still useful, but they now support the broader workflow story instead of pretending to be the whole product.</p>
            </div>
            <span class="section-note">{total_repos} repos scored</span>
          </div>
          {table_html}
        </div>"""
        body += self._recently_scored_fetch_script()

        meta = PageMeta(
            title="agentkit — Canonical source and guardrails for AI coding agents",
            description="Write one canonical source for AI coding agents, project it into AGENTS.md and other agent files, add execution contracts, and score agent-readiness with agentkit-cli.",
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

    def _recently_scored_fetch_script(self) -> str:
        return """
<script>
(function() {
  function gradeClass(g) {
    return {'A':'grade-a','B':'grade-b','C':'grade-c','D':'grade-d','F':'grade-f'}[g] || '';
  }
  function renderRecentlyScored(data) {
    var el = document.getElementById('recently-scored-list');
    if (!el) return;
    if (!data || !data.repos || !data.repos.length) {
      el.innerHTML = '<p class="loading-msg">No data available.</p>';
      return;
    }
    var top = data.repos.slice(0, 5);
    var html = '<ul class="repo-list">';
    top.forEach(function(r) {
      var src = r.source || 'ecosystem';
      var srcLabel = src === 'community' ? 'community' : src === 'manual' ? 'manual' : 'ecosystem';
      var srcClass = 'source-' + srcLabel;
      html += '<li class="repo-item">'
        + '<a href="' + r.url + '" target="_blank" rel="noopener" class="repo-name">' + r.name + '</a>'
        + '<span class="eco-badge">' + (r.ecosystem || '') + '</span>'
        + '<span class="source-badge ' + srcClass + '">' + srcLabel + '</span>'
        + '<span class="score-val">' + r.score + '</span>'
        + '<span class="grade ' + gradeClass(r.grade) + '">' + r.grade + '</span>'
        + '</li>';
    });
    html += '</ul>';
    if (data.stats) {
      html += '<p class="data-ts">Updated: ' + (data.generated_at ? data.generated_at.slice(0,10) : '') + '</p>';
    }
    el.innerHTML = html;
    var statEl = document.getElementById('repos-scored-stat') || document.querySelector('.stat-num');
    if (statEl && data.stats && data.stats.total) statEl.textContent = data.stats.total;
    var communityCount = (data.repos || []).filter(function(r) { return r.source === 'community'; }).length;
    var commEl = document.getElementById('community-scored-stat');
    if (commEl) commEl.textContent = communityCount;
    var badge = document.querySelector('.hero-badge');
    if (badge && data.stats && data.stats.total) {
      badge.textContent = badge.textContent.replace(/\\d+ repos scored/, data.stats.total + ' repos scored');
    }
  }
  fetch('/agentkit-cli/data.json')
    .then(function(r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(renderRecentlyScored)
    .catch(function() {
      var el = document.getElementById('recently-scored-list');
      if (el) el.innerHTML = '<p class="loading-msg">Score data unavailable.</p>';
    });
})();
</script>"""

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
