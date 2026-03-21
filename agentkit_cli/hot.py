"""agentkit hot — GitHub trending repos scored via ExistingStateScorer."""
from __future__ import annotations

import re
import tempfile
import shutil
from dataclasses import dataclass, asdict, field
try:
    import requests as _requests_module
except ImportError:
    _requests_module = None  # type: ignore
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class HotRepoResult:
    """Score result for a single trending repo."""
    full_name: str
    rank: int
    score: Optional[float]
    grade: Optional[str]
    description: str = ""
    stars: int = 0
    language: str = ""
    score_details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class HotResult:
    """Full result from `agentkit hot`."""
    repos: list[HotRepoResult]
    most_surprising: Optional[HotRepoResult]
    tweet_text: str
    run_date: str
    language_filter: Optional[str]
    share_url: Optional[str] = None
    trending_available: bool = True

    def to_dict(self) -> dict:
        return {
            "repos": [r.to_dict() for r in self.repos],
            "most_surprising": self.most_surprising.to_dict() if self.most_surprising else None,
            "tweet_text": self.tweet_text,
            "run_date": self.run_date,
            "language_filter": self.language_filter,
            "share_url": self.share_url,
            "trending_available": self.trending_available,
        }


# ---------------------------------------------------------------------------
# Trending fetch
# ---------------------------------------------------------------------------

_FALLBACK_REPOS = [
    {"full_name": "langchain-ai/langchain", "description": "Build LLM apps", "stars": 90000, "language": "Python"},
    {"full_name": "fastapi/fastapi", "description": "Fast web framework", "stars": 75000, "language": "Python"},
    {"full_name": "vercel/next.js", "description": "React framework", "stars": 120000, "language": "JavaScript"},
    {"full_name": "microsoft/vscode", "description": "Code editor", "stars": 160000, "language": "TypeScript"},
    {"full_name": "django/django", "description": "Web framework", "stars": 78000, "language": "Python"},
    {"full_name": "facebook/react", "description": "UI library", "stars": 220000, "language": "JavaScript"},
    {"full_name": "psf/requests", "description": "HTTP for Humans", "stars": 51000, "language": "Python"},
    {"full_name": "pallets/flask", "description": "WSGI framework", "stars": 67000, "language": "Python"},
    {"full_name": "encode/httpx", "description": "Async HTTP client", "stars": 13000, "language": "Python"},
    {"full_name": "tiangolo/fastapi", "description": "FastAPI", "stars": 75000, "language": "Python"},
]


def fetch_github_trending(language: Optional[str] = None, limit: int = 10) -> tuple[list[dict], bool]:
    """Fetch GitHub trending repos. Returns (repos, available)."""
    try:
        requests = _requests_module
        if requests is None:
            raise ImportError("requests not available")
        url = "https://github.com/trending"
        if language:
            url += f"/{language.lower()}"
        url += "?since=daily"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "agentkit-cli/0.81.0"})
        if resp.status_code != 200:
            return _FALLBACK_REPOS[:limit], False

        repos = _parse_trending_html(resp.text, limit=limit)
        if not repos:
            return _FALLBACK_REPOS[:limit], False
        return repos, True
    except Exception:
        return _FALLBACK_REPOS[:limit], False


def _parse_trending_html(html: str, limit: int = 25) -> list[dict]:
    """Parse GitHub trending HTML to extract repo info."""
    repos = []
    # Match article tags for trending repos
    article_pattern = re.compile(r'<article[^>]*class="[^"]*Box-row[^"]*"[^>]*>(.*?)</article>', re.DOTALL)
    articles = article_pattern.findall(html)

    for i, article in enumerate(articles[:limit]):
        if i >= limit:
            break

        # Extract repo name from h2 link
        name_match = re.search(r'href="/([^/"]+/[^/"]+)"[^>]*>\s*(?:<span[^>]*>[^<]*</span>)?\s*([^<\n]+)', article)
        if not name_match:
            # Try simpler pattern
            name_match2 = re.search(r'<h2[^>]*>.*?href="/([^"]+)"', article, re.DOTALL)
            if not name_match2:
                continue
            full_name = name_match2.group(1).strip().strip("/")
        else:
            full_name = name_match.group(1).strip()

        # Clean up
        full_name = full_name.strip("/")
        if "/" not in full_name or full_name.count("/") > 1:
            continue
        # Skip sponsor/ads entries
        owner = full_name.split("/")[0].lower()
        if owner in ("sponsors", "orgs", "topics", "trending"):
            continue

        # Description
        desc_match = re.search(r'<p[^>]*class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>', article, re.DOTALL)
        description = ""
        if desc_match:
            description = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()

        # Stars (today's stars from "stars today" span or total)
        stars = 0
        stars_match = re.search(r'([\d,]+)\s*stars today', article)
        if stars_match:
            stars = int(stars_match.group(1).replace(",", ""))
        else:
            stars_match2 = re.search(r'<svg[^>]*octicon-star[^>]*>.*?</svg>\s*([\d,]+)', article, re.DOTALL)
            if stars_match2:
                stars = int(stars_match2.group(1).replace(",", ""))

        # Language
        lang_match = re.search(r'itemprop="programmingLanguage"[^>]*>([^<]+)<', article)
        language = lang_match.group(1).strip() if lang_match else ""

        repos.append({
            "full_name": full_name,
            "description": description,
            "stars": stars,
            "language": language,
        })

    return repos


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _score_repo(full_name: str, timeout: int = 60) -> tuple[Optional[float], Optional[str], dict]:
    """Clone and score a GitHub repo with ExistingStateScorer. Returns (score, grade, details)."""
    from agentkit_cli.existing_scorer import ExistingStateScorer

    tmpdir = tempfile.mkdtemp(prefix="agentkit_hot_")
    try:
        import subprocess
        url = f"https://github.com/{full_name}.git"
        result = subprocess.run(
            ["git", "clone", "--depth=1", "--quiet", url, tmpdir],
            capture_output=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            return None, None, {}

        scorer = ExistingStateScorer(Path(tmpdir))
        score_dict = scorer.score_all()
        score = score_dict.get("composite")
        grade = _grade_from_score(score) if score is not None else None

        # Dimension details (exclude composite)
        details = {k: v for k, v in score_dict.items() if k != "composite"}

        return score, grade, details
    except Exception:
        return None, None, {}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _grade_from_score(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _find_most_surprising(repos: list[HotRepoResult]) -> Optional[HotRepoResult]:
    """Find the most interesting/surprising result.

    Surprising = top-ranked (low rank number) with low score, OR highly scored with high stars.
    """
    scored = [r for r in repos if r.score is not None]
    if not scored:
        return repos[0] if repos else None

    # Top-ranked (rank 1-3) with lowest score
    top_repos = [r for r in scored if r.rank <= 3]
    if top_repos:
        # Most surprising: highest rank + lowest score
        candidate_low = min(top_repos, key=lambda r: (r.score or 100))
        if (candidate_low.score or 100) < 50:
            return candidate_low

    # Or: highest scored (could be surprising if also #1 trending)
    candidate_high = max(scored, key=lambda r: (r.score or 0))
    if (candidate_high.score or 0) >= 80 and candidate_high.rank <= 5:
        return candidate_high

    # Fallback: lowest scored top-5
    top5 = sorted([r for r in scored if r.rank <= 5], key=lambda r: r.score or 0)
    if top5:
        return top5[0]

    return scored[0]


def _build_tweet_text(repos: list[HotRepoResult], most_surprising: Optional[HotRepoResult],
                      language_filter: Optional[str]) -> str:
    """Build tweet text ≤280 chars."""
    lang_str = f" ({language_filter})" if language_filter else ""

    if most_surprising and most_surprising.score is not None:
        short_name = most_surprising.full_name.split("/")[-1]
        score = int(most_surprising.score)
        rank = most_surprising.rank

        if score < 45:
            # Low score trending repo
            tweet = (
                f"#{rank} trending on GitHub today: {short_name} scores {score}/100 on agent-readiness "
                f"— missing key docs context. High traffic, low agent signal."
            )
        elif score >= 80:
            # High score
            tweet = (
                f"{short_name} is #{rank} trending on GitHub{lang_str} and already agent-ready "
                f"({score}/100). Good context for LLM tooling."
            )
        else:
            tweet = (
                f"{short_name} hits #{rank} trending on GitHub{lang_str} with a {score}/100 "
                f"agent-readiness score. Room to improve."
            )
    else:
        # Generic fallback
        names = [r.full_name.split("/")[-1] for r in repos[:3] if r.score is not None]
        if names:
            tweet = f"Today's GitHub trending{lang_str}: scored {', '.join(names)} for agent-readiness. Results may surprise you."
        else:
            tweet = f"Checked today's GitHub trending repos{lang_str} for agent-readiness. Fetch unavailable — using popular repos as baseline."

    # Trim to 280
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."
    return tweet


# ---------------------------------------------------------------------------
# HTML report
# ---------------------------------------------------------------------------

def render_hot_html(result: HotResult) -> str:
    """Render dark-theme HTML report for hot results."""
    rows = ""
    for repo in result.repos:
        score_str = f"{repo.score:.0f}" if repo.score is not None else "N/A"
        grade_str = repo.grade or "N/A"
        surprise = "⭐ " if result.most_surprising and repo.full_name == result.most_surprising.full_name else ""
        rows += f"""
        <tr>
            <td>{surprise}{repo.rank}</td>
            <td><a href="https://github.com/{repo.full_name}" style="color:#58a6ff">{repo.full_name}</a></td>
            <td>{repo.language}</td>
            <td class="score">{score_str}</td>
            <td class="grade grade-{grade_str}">{grade_str}</td>
            <td>{repo.stars:,}</td>
            <td class="desc">{repo.description[:80]}</td>
        </tr>"""

    surprise_block = ""
    if result.most_surprising and result.most_surprising.score is not None:
        ms = result.most_surprising
        surprise_block = f"""
        <div class="surprise">
            <h2>⭐ Most Surprising: {ms.full_name}</h2>
            <p>Rank #{ms.rank} trending · Score: {ms.score:.0f}/100 · Grade: {ms.grade}</p>
            <p class="tweet">{result.tweet_text}</p>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>agentkit hot — {result.run_date[:10]}</title>
<style>
body {{ background: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 2rem; }}
h1 {{ color: #f0f6fc; }}
.surprise {{ background: #161b22; border: 1px solid #30363d; border-left: 4px solid #f78166; padding: 1rem 1.5rem; border-radius: 6px; margin-bottom: 2rem; }}
.surprise h2 {{ color: #f78166; margin: 0 0 0.5rem; }}
.tweet {{ color: #8b949e; font-style: italic; }}
table {{ border-collapse: collapse; width: 100%; }}
th {{ background: #161b22; color: #8b949e; padding: 0.5rem 1rem; text-align: left; border-bottom: 1px solid #30363d; }}
td {{ padding: 0.5rem 1rem; border-bottom: 1px solid #21262d; }}
.score {{ font-weight: bold; color: #e3b341; }}
.grade {{ font-weight: bold; }}
.grade-A {{ color: #3fb950; }}
.grade-B {{ color: #58a6ff; }}
.grade-C {{ color: #e3b341; }}
.grade-D {{ color: #f78166; }}
.grade-F {{ color: #f85149; }}
.desc {{ color: #8b949e; font-size: 0.9em; }}
</style>
</head>
<body>
<h1>🔥 agentkit hot — GitHub Trending Agent-Readiness</h1>
<p style="color:#8b949e">Generated: {result.run_date} · Language: {result.language_filter or 'all'}</p>
{surprise_block}
<table>
<thead><tr><th>Rank</th><th>Repo</th><th>Language</th><th>Score</th><th>Grade</th><th>Stars Today</th><th>Description</th></tr></thead>
<tbody>{rows}
</tbody>
</table>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class HotEngine:
    """Core engine for `agentkit hot`."""

    def __init__(self, timeout: int = 60, token: Optional[str] = None):
        self.timeout = timeout
        self.token = token

    def run(
        self,
        language: Optional[str] = None,
        limit: int = 10,
        _fetch_fn=None,
        _score_fn=None,
    ) -> HotResult:
        """Fetch trending, score, return HotResult."""
        limit = min(limit, 25)
        fetch_fn = _fetch_fn or fetch_github_trending
        score_fn = _score_fn or _score_repo

        repos_raw, available = fetch_fn(language=language, limit=limit)

        repo_results: list[HotRepoResult] = []
        for i, r in enumerate(repos_raw):
            full_name = r.get("full_name", "")
            score, grade, details = score_fn(full_name, self.timeout)
            if score is not None and grade is None:
                grade = _grade_from_score(score)

            repo_results.append(HotRepoResult(
                full_name=full_name,
                rank=i + 1,
                score=score,
                grade=grade,
                description=r.get("description", ""),
                stars=r.get("stars", 0),
                language=r.get("language", ""),
                score_details=details,
            ))

        most_surprising = _find_most_surprising(repo_results)
        tweet = _build_tweet_text(repo_results, most_surprising, language)

        return HotResult(
            repos=repo_results,
            most_surprising=most_surprising,
            tweet_text=tweet,
            run_date=datetime.now(timezone.utc).isoformat(),
            language_filter=language,
            trending_available=available,
        )
