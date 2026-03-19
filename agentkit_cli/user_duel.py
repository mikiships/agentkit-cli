"""agentkit user-duel engine — head-to-head agent-readiness comparison for two GitHub users."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from agentkit_cli.user_scorecard import UserScorecardEngine, UserScorecardResult, score_to_grade


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DuelDimension:
    """Result for a single comparison dimension."""
    name: str
    user1_value: float
    user2_value: float
    winner: str  # "user1", "user2", "tie"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "user1_value": self.user1_value,
            "user2_value": self.user2_value,
            "winner": self.winner,
        }


@dataclass
class UserDuelResult:
    """Full result of a user-duel comparison."""
    user1: str
    user2: str
    user1_scorecard: UserScorecardResult
    user2_scorecard: UserScorecardResult
    dimensions: list[DuelDimension] = field(default_factory=list)
    overall_winner: str = "tie"  # "user1", "user2", "tie"
    tied: bool = False
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "user1": self.user1,
            "user2": self.user2,
            "user1_scorecard": self.user1_scorecard.to_dict(),
            "user2_scorecard": self.user2_scorecard.to_dict(),
            "dimensions": [d.to_dict() for d in self.dimensions],
            "overall_winner": self.overall_winner,
            "tied": self.tied,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class UserDuelEngine:
    """Compare two GitHub users' agent-readiness scores."""

    def __init__(
        self,
        limit: int = 10,
        token: Optional[str] = None,
        timeout: int = 60,
        _engine_factory=None,
    ) -> None:
        self.limit = limit
        self.token = token
        self.timeout = timeout
        # Test override: callable(username, limit, token, timeout) -> UserScorecardEngine
        self._engine_factory = _engine_factory

    def _make_engine(self, username: str) -> UserScorecardEngine:
        if self._engine_factory is not None:
            return self._engine_factory(username, self.limit, self.token, self.timeout)
        return UserScorecardEngine(
            username=username,
            limit=self.limit,
            token=self.token,
            timeout=self.timeout,
        )

    def run(
        self,
        user1: str,
        user2: str,
        progress_callback=None,
    ) -> UserDuelResult:
        """Fetch scorecards for both users and compare them."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        engine1 = self._make_engine(user1)
        engine2 = self._make_engine(user2)

        def _cb1(full_name: str, score_str: str) -> None:
            if progress_callback:
                progress_callback(user1, full_name, score_str)

        def _cb2(full_name: str, score_str: str) -> None:
            if progress_callback:
                progress_callback(user2, full_name, score_str)

        scorecard1 = engine1.run(progress_callback=_cb1)
        scorecard2 = engine2.run(progress_callback=_cb2)

        dimensions = self._compare_dimensions(scorecard1, scorecard2)
        overall_winner, tied = self._determine_overall_winner(dimensions)

        return UserDuelResult(
            user1=user1,
            user2=user2,
            user1_scorecard=scorecard1,
            user2_scorecard=scorecard2,
            dimensions=dimensions,
            overall_winner=overall_winner,
            tied=tied,
            timestamp=timestamp,
        )

    def _compare_dimensions(
        self,
        s1: UserScorecardResult,
        s2: UserScorecardResult,
    ) -> list[DuelDimension]:
        """Compute per-dimension winners."""
        dims: list[DuelDimension] = []

        # avg_score
        dims.append(_make_dim("avg_score", s1.avg_score, s2.avg_score, higher_wins=True))

        # letter_grade (A=4, B=3, C=2, D=1)
        grade_map = {"A": 4, "B": 3, "C": 2, "D": 1}
        g1 = grade_map.get(s1.grade, 0)
        g2 = grade_map.get(s2.grade, 0)
        dims.append(_make_dim("letter_grade", float(g1), float(g2), higher_wins=True))

        # repo_count (analyzed repos)
        dims.append(_make_dim("repo_count", float(s1.analyzed_repos), float(s2.analyzed_repos), higher_wins=True))

        # agent_ready_repos (repos with context files)
        ar1 = sum(1 for r in s1.all_repos if r.has_context)
        ar2 = sum(1 for r in s2.all_repos if r.has_context)
        dims.append(_make_dim("agent_ready_repos", float(ar1), float(ar2), higher_wins=True))

        return dims

    def _determine_overall_winner(
        self,
        dimensions: list[DuelDimension],
    ) -> tuple[str, bool]:
        """Return (overall_winner, tied). Winner is whoever wins most dimensions."""
        u1_wins = sum(1 for d in dimensions if d.winner == "user1")
        u2_wins = sum(1 for d in dimensions if d.winner == "user2")
        if u1_wins > u2_wins:
            return "user1", False
        if u2_wins > u1_wins:
            return "user2", False
        return "tie", True


def _make_dim(name: str, v1: float, v2: float, higher_wins: bool = True) -> DuelDimension:
    """Create a DuelDimension with winner determined."""
    if higher_wins:
        if v1 > v2:
            winner = "user1"
        elif v2 > v1:
            winner = "user2"
        else:
            winner = "tie"
    else:
        if v1 < v2:
            winner = "user1"
        elif v2 < v1:
            winner = "user2"
        else:
            winner = "tie"
    return DuelDimension(name=name, user1_value=v1, user2_value=v2, winner=winner)


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------

_DUEL_GRADE_COLORS = {
    "A": "#3fb950",
    "B": "#58a6ff",
    "C": "#d29922",
    "D": "#f85149",
}

_WINNER_COLOR = "#3fb950"
_LOSER_COLOR = "#8b949e"
_TIE_COLOR = "#d29922"


def _grade_color(grade: str) -> str:
    return _DUEL_GRADE_COLORS.get(grade, "#8b949e")


class UserDuelReportRenderer:
    """Generate a self-contained dark-theme HTML duel report."""

    def render(self, result: UserDuelResult, timestamp: Optional[str] = None) -> str:
        if timestamp is None:
            timestamp = result.timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        u1 = result.user1
        u2 = result.user2
        s1 = result.user1_scorecard
        s2 = result.user2_scorecard

        avatar1 = f"https://github.com/{u1}.png"
        avatar2 = f"https://github.com/{u2}.png"

        if result.tied:
            verdict_html = f'<div class="verdict tie">🤝 Tied!</div>'
        elif result.overall_winner == "user1":
            verdict_html = f'<div class="verdict win">🏆 @{u1} wins!</div>'
        else:
            verdict_html = f'<div class="verdict win">🏆 @{u2} wins!</div>'

        dim_rows = ""
        for dim in result.dimensions:
            u1_val = _fmt_dim_value(dim.name, dim.user1_value)
            u2_val = _fmt_dim_value(dim.name, dim.user2_value)
            if dim.winner == "user1":
                u1_style = f'style="color:{_WINNER_COLOR};font-weight:bold"'
                u2_style = f'style="color:{_LOSER_COLOR}"'
                winner_cell = f'<td style="color:{_WINNER_COLOR}">@{u1}</td>'
            elif dim.winner == "user2":
                u1_style = f'style="color:{_LOSER_COLOR}"'
                u2_style = f'style="color:{_WINNER_COLOR};font-weight:bold"'
                winner_cell = f'<td style="color:{_WINNER_COLOR}">@{u2}</td>'
            else:
                u1_style = f'style="color:{_TIE_COLOR}"'
                u2_style = f'style="color:{_TIE_COLOR}"'
                winner_cell = f'<td style="color:{_TIE_COLOR}">tie</td>'
            dim_rows += f"""
            <tr>
              <td>{dim.name.replace("_", " ").title()}</td>
              <td {u1_style}>{u1_val}</td>
              <td {u2_style}>{u2_val}</td>
              {winner_cell}
            </tr>"""

        # Top 5 repos for each user
        top5_u1 = s1.all_repos[:5]
        top5_u2 = s2.all_repos[:5]

        def repo_cards(repos, username):
            cards = ""
            for repo in repos:
                score_str = f"{repo.score:.0f}" if repo.score is not None else "—"
                ctx = "✓" if repo.has_context else "✗"
                gc = _grade_color(repo.grade)
                cards += f"""
            <div class="repo-card">
              <span class="repo-name">{repo.name}</span>
              <span class="repo-score" style="color:{gc}">{score_str}</span>
              <span class="repo-grade" style="color:{gc}">{repo.grade}</span>
              <span class="repo-ctx">{ctx}</span>
            </div>"""
            return cards or "<p style='color:#8b949e'>No repos analyzed.</p>"

        u1_repos_html = repo_cards(top5_u1, u1)
        u2_repos_html = repo_cards(top5_u2, u2)

        gc1 = _grade_color(s1.grade)
        gc2 = _grade_color(s2.grade)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⚔️ Agent Readiness Duel — @{u1} vs @{u2}</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    background: #0d1117;
    color: #e6edf3;
    font-family: 'Courier New', Courier, monospace;
    min-height: 100vh;
    padding: 2rem;
}}
.container {{ max-width: 960px; margin: 0 auto; }}
h1 {{ font-size: 1.6rem; color: #58a6ff; text-align: center; margin-bottom: 0.5rem; }}
.subtitle {{ text-align: center; font-size: 0.85rem; color: #8b949e; margin-bottom: 2rem; }}
.combatants {{ display: flex; justify-content: center; gap: 3rem; margin-bottom: 2rem; }}
.combatant {{ text-align: center; }}
.combatant img {{ width: 80px; height: 80px; border-radius: 50%; border: 2px solid #30363d; }}
.combatant .name {{ color: #58a6ff; font-weight: bold; margin-top: 0.5rem; }}
.combatant .grade {{ font-size: 1.2rem; font-weight: bold; margin-top: 0.25rem; }}
.vs {{ display: flex; align-items: center; color: #8b949e; font-size: 1.5rem; font-weight: bold; }}
table {{ width: 100%; border-collapse: collapse; margin-bottom: 2rem; }}
th {{ background: #161b22; padding: 0.6rem 1rem; text-align: left; color: #8b949e; border-bottom: 1px solid #30363d; }}
td {{ padding: 0.5rem 1rem; border-bottom: 1px solid #21262d; }}
.verdict {{ text-align: center; font-size: 1.4rem; font-weight: bold; padding: 1.2rem; border-radius: 8px; margin-bottom: 2rem; }}
.verdict.win {{ background: #0e2a1f; color: {_WINNER_COLOR}; border: 1px solid {_WINNER_COLOR}; }}
.verdict.tie {{ background: #1a1500; color: {_TIE_COLOR}; border: 1px solid {_TIE_COLOR}; }}
.repos-section {{ display: flex; gap: 2rem; margin-bottom: 2rem; }}
.repos-col {{ flex: 1; }}
.repos-col h3 {{ color: #58a6ff; margin-bottom: 1rem; }}
.repo-card {{ display: flex; align-items: center; gap: 0.75rem; padding: 0.4rem 0; border-bottom: 1px solid #21262d; }}
.repo-name {{ flex: 1; color: #e6edf3; font-size: 0.85rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.repo-score, .repo-grade {{ width: 2rem; text-align: right; font-size: 0.85rem; }}
.repo-ctx {{ width: 1.5rem; text-align: center; color: #3fb950; }}
.footer {{ text-align: center; color: #8b949e; font-size: 0.75rem; margin-top: 2rem; }}
</style>
</head>
<body>
<div class="container">
  <h1>⚔️ Agent Readiness Duel</h1>
  <p class="subtitle">Generated {timestamp}</p>

  <div class="combatants">
    <div class="combatant">
      <img src="{avatar1}" alt="@{u1}" onerror="this.style.display='none'">
      <div class="name">@{u1}</div>
      <div class="grade" style="color:{gc1}">Grade {s1.grade} · {s1.avg_score:.1f}</div>
    </div>
    <div class="vs">VS</div>
    <div class="combatant">
      <img src="{avatar2}" alt="@{u2}" onerror="this.style.display='none'">
      <div class="name">@{u2}</div>
      <div class="grade" style="color:{gc2}">Grade {s2.grade} · {s2.avg_score:.1f}</div>
    </div>
  </div>

  {verdict_html}

  <table>
    <thead><tr><th>Dimension</th><th>@{u1}</th><th>@{u2}</th><th>Winner</th></tr></thead>
    <tbody>{dim_rows}</tbody>
  </table>

  <div class="repos-section">
    <div class="repos-col">
      <h3>@{u1} — Top Repos</h3>
      {u1_repos_html}
    </div>
    <div class="repos-col">
      <h3>@{u2} — Top Repos</h3>
      {u2_repos_html}
    </div>
  </div>

  <div class="footer">Powered by agentkit-cli</div>
</div>
</body>
</html>"""
        return html


def _fmt_dim_value(name: str, value: float) -> str:
    """Format a dimension value for display."""
    if name == "letter_grade":
        grade_map_rev = {4: "A", 3: "B", 2: "C", 1: "D", 0: "D"}
        return grade_map_rev.get(int(value), "D")
    if name in ("avg_score",):
        return f"{value:.1f}"
    return str(int(value))


def publish_user_duel(result: UserDuelResult) -> Optional[str]:
    """Render and publish a user duel report to here.now. Returns URL or None."""
    try:
        from agentkit_cli.publish import (
            PublishError,
            _json_post,
            _put_file,
            _finalize,
            HERENOW_API_BASE,
        )
        renderer = UserDuelReportRenderer()
        html = renderer.render(result)
        payload = _json_post(
            f"{HERENOW_API_BASE}/api/v1/publish",
            {"files": [{"path": "index.html", "content_type": "text/html"}]},
        )
        upload_url = payload["files"][0]["upload_url"]
        pub_id = payload["id"]
        _put_file(upload_url, html.encode("utf-8"), "text/html")
        final = _finalize(f"{HERENOW_API_BASE}/api/v1/publish/{pub_id}/finalize")
        return final.get("url")
    except Exception:
        return None
