"""Tests for D1/D2/D3: pages-refresh command, workflow, and index.html."""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from agentkit_cli.commands.pages_refresh import (
    build_data_json,
    pages_refresh_command,
    score_to_grade,
    update_index_html,
)

# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def _make_entry(name="org/repo", score=75.0, grade="B", eco="python"):
    from agentkit_cli.leaderboard_page import LeaderboardEntry
    return LeaderboardEntry(rank=1, repo_full_name=name, score=score, grade=grade, stars=500, ecosystem=eco)


def _make_result(ecosystems=None):
    from agentkit_cli.leaderboard_page import EcosystemLeaderboard, LeaderboardPageResult
    if ecosystems is None:
        ecosystems = [
            EcosystemLeaderboard(
                ecosystem="python",
                entries=[
                    _make_entry("openai/openai-python", 91.0, "A", "python"),
                    _make_entry("pydantic/pydantic", 72.0, "B", "python"),
                ],
            ),
            EcosystemLeaderboard(
                ecosystem="typescript",
                entries=[
                    _make_entry("vercel/ai", 80.0, "A", "typescript"),
                ],
            ),
        ]
    return LeaderboardPageResult(ecosystems=ecosystems)


# ---------------------------------------------------------------------------
# D1: score_to_grade
# ---------------------------------------------------------------------------

class TestScoreToGrade:
    def test_a_grade(self):
        assert score_to_grade(85) == "A"

    def test_a_boundary(self):
        assert score_to_grade(80) == "A"

    def test_b_grade(self):
        assert score_to_grade(70) == "B"

    def test_c_grade(self):
        assert score_to_grade(55) == "C"

    def test_d_grade(self):
        assert score_to_grade(40) == "D"

    def test_f_grade(self):
        assert score_to_grade(20) == "F"


# ---------------------------------------------------------------------------
# D1: build_data_json
# ---------------------------------------------------------------------------

class TestBuildDataJson:
    def test_structure_keys(self):
        result = _make_result()
        data = build_data_json(result)
        assert "generated_at" in data
        assert "repos" in data
        assert "stats" in data

    def test_repos_have_required_fields(self):
        result = _make_result()
        data = build_data_json(result)
        for repo in data["repos"]:
            assert "name" in repo
            assert "url" in repo
            assert "score" in repo
            assert "grade" in repo
            assert "ecosystem" in repo

    def test_url_is_github(self):
        result = _make_result()
        data = build_data_json(result)
        for repo in data["repos"]:
            assert repo["url"].startswith("https://github.com/")

    def test_stats_fields(self):
        result = _make_result()
        data = build_data_json(result)
        assert "total" in data["stats"]
        assert "median" in data["stats"]
        assert "top_score" in data["stats"]

    def test_stats_total_matches_repos(self):
        result = _make_result()
        data = build_data_json(result)
        assert data["stats"]["total"] == len(data["repos"])

    def test_no_duplicate_repos(self):
        result = _make_result()
        data = build_data_json(result)
        names = [r["name"] for r in data["repos"]]
        assert len(names) == len(set(names))

    def test_top_score_is_max(self):
        result = _make_result()
        data = build_data_json(result)
        scores = [r["score"] for r in data["repos"]]
        assert data["stats"]["top_score"] == max(scores)

    def test_generated_at_is_iso(self):
        result = _make_result()
        data = build_data_json(result)
        # Should be parseable ISO datetime
        from datetime import datetime
        dt = datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))
        assert dt is not None

    def test_ecosystem_preserved(self):
        result = _make_result()
        data = build_data_json(result)
        ecosystems = {r["ecosystem"] for r in data["repos"]}
        assert "python" in ecosystems


# ---------------------------------------------------------------------------
# D1: update_index_html
# ---------------------------------------------------------------------------

MINIMAL_HTML = """\
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
  <div class="hero-badge">v0.93.0 &middot; 0 repos scored</div>
  <div class="stat-num" id="repos-scored-stat">0</div><div class="stat-label">Repos Scored</div>
  <section class="pipeline-section"><div>pipe</div></section>
</body>
</html>"""


class TestUpdateIndexHtml:
    def _write_html(self, tmp_path: Path, content: str) -> Path:
        p = tmp_path / "index.html"
        p.write_text(content)
        return p

    def test_returns_true_when_changed(self, tmp_path):
        p = self._write_html(tmp_path, MINIMAL_HTML)
        data = {"stats": {"total": 10, "median": 75.0, "top_score": 91.0}}
        result = update_index_html(p, data)
        assert result is True

    def test_hero_badge_updated(self, tmp_path):
        p = self._write_html(tmp_path, MINIMAL_HTML)
        data = {"stats": {"total": 42, "median": 75.0, "top_score": 91.0}}
        update_index_html(p, data)
        html = p.read_text()
        assert "42 repos scored" in html

    def test_stat_num_updated(self, tmp_path):
        p = self._write_html(tmp_path, MINIMAL_HTML)
        data = {"stats": {"total": 15, "median": 70.0, "top_score": 88.0}}
        update_index_html(p, data)
        html = p.read_text()
        assert ">15<" in html

    def test_recently_scored_section_injected(self, tmp_path):
        p = self._write_html(tmp_path, MINIMAL_HTML)
        data = {"stats": {"total": 5, "median": 70.0, "top_score": 88.0}}
        update_index_html(p, data)
        html = p.read_text()
        assert 'id="recently-scored"' in html

    def test_fetch_script_injected(self, tmp_path):
        p = self._write_html(tmp_path, MINIMAL_HTML)
        data = {"stats": {"total": 5, "median": 70.0, "top_score": 88.0}}
        update_index_html(p, data)
        html = p.read_text()
        assert "renderRecentlyScored" in html

    def test_returns_false_for_nonexistent_file(self, tmp_path):
        p = tmp_path / "nonexistent.html"
        data = {"stats": {"total": 5, "median": 70.0, "top_score": 88.0}}
        result = update_index_html(p, data)
        assert result is False


# ---------------------------------------------------------------------------
# D1: pages_refresh_command (with mocked engine)
# ---------------------------------------------------------------------------

class TestPagesRefreshCommand:
    def _make_engine(self):
        result = _make_result()
        engine = MagicMock()
        engine.run.return_value = result
        return engine

    def test_writes_data_json(self, tmp_path):
        (tmp_path / "index.html").write_text(MINIMAL_HTML)
        pages_refresh_command(docs_dir=tmp_path, _engine_factory=lambda *a: self._make_engine())
        assert (tmp_path / "data.json").exists()

    def test_data_json_valid(self, tmp_path):
        (tmp_path / "index.html").write_text(MINIMAL_HTML)
        data = pages_refresh_command(docs_dir=tmp_path, _engine_factory=lambda *a: self._make_engine())
        json_data = json.loads((tmp_path / "data.json").read_text())
        assert "repos" in json_data
        assert "stats" in json_data

    def test_writes_leaderboard_html(self, tmp_path):
        (tmp_path / "index.html").write_text(MINIMAL_HTML)
        pages_refresh_command(docs_dir=tmp_path, _engine_factory=lambda *a: self._make_engine())
        assert (tmp_path / "leaderboard.html").exists()

    def test_returns_data_dict(self, tmp_path):
        (tmp_path / "index.html").write_text(MINIMAL_HTML)
        result = pages_refresh_command(docs_dir=tmp_path, _engine_factory=lambda *a: self._make_engine())
        assert isinstance(result, dict)
        assert "repos" in result

    def test_creates_docs_dir(self, tmp_path):
        new_dir = tmp_path / "newdocs"
        pages_refresh_command(docs_dir=new_dir, _engine_factory=lambda *a: self._make_engine())
        assert new_dir.exists()


# ---------------------------------------------------------------------------
# D1: CLI registration
# ---------------------------------------------------------------------------

class TestCliRegistration:
    def test_pages_refresh_help(self):
        from typer.testing import CliRunner
        from agentkit_cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["pages-refresh", "--help"])
        assert result.exit_code == 0
        assert "pages-refresh" in result.output or "Refresh" in result.output

    def test_pages_refresh_in_commands(self):
        from typer.testing import CliRunner
        from agentkit_cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert "pages-refresh" in result.output


# ---------------------------------------------------------------------------
# D2: Workflow file tests
# ---------------------------------------------------------------------------

WORKFLOW_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "daily-pages-refresh.yml"


class TestWorkflowFile:
    def test_file_exists(self):
        assert WORKFLOW_PATH.exists(), "daily-pages-refresh.yml must exist"

    def test_valid_yaml(self):
        data = yaml.safe_load(WORKFLOW_PATH.read_text())
        assert data is not None

    def test_has_cron_schedule(self):
        content = WORKFLOW_PATH.read_text()
        assert "0 8 * * *" in content

    def test_has_workflow_dispatch(self):
        content = WORKFLOW_PATH.read_text()
        assert "workflow_dispatch" in content

    def test_installs_agentkit_cli(self):
        content = WORKFLOW_PATH.read_text()
        assert "agentkit-cli" in content or "agentkit_cli" in content

    def test_runs_pages_refresh(self):
        content = WORKFLOW_PATH.read_text()
        assert "pages-refresh" in content

    def test_commit_message_skip_ci(self):
        content = WORKFLOW_PATH.read_text()
        assert "[skip ci]" in content

    def test_uses_github_token(self):
        content = WORKFLOW_PATH.read_text()
        assert "GITHUB_TOKEN" in content


# ---------------------------------------------------------------------------
# D3: docs/index.html tests
# ---------------------------------------------------------------------------

INDEX_PATH = Path(__file__).parent.parent / "docs" / "index.html"


class TestIndexHtml:
    def test_file_exists(self):
        assert INDEX_PATH.exists()

    def test_has_fetch_script(self):
        html = INDEX_PATH.read_text()
        assert "fetch(" in html and "data.json" in html

    def test_has_render_function(self):
        html = INDEX_PATH.read_text()
        assert "renderRecentlyScored" in html

    def test_has_recently_scored_section(self):
        html = INDEX_PATH.read_text()
        assert 'id="recently-scored"' in html

    def test_has_repos_scored_stat_id(self):
        html = INDEX_PATH.read_text()
        assert 'repos-scored-stat' in html

    def test_fetch_uses_agentkit_cli_path(self):
        html = INDEX_PATH.read_text()
        assert "/agentkit-cli/data.json" in html

    def test_renders_grade_classes(self):
        html = INDEX_PATH.read_text()
        assert "grade-a" in html or "gradeClass" in html

    def test_handles_fetch_error(self):
        html = INDEX_PATH.read_text()
        assert ".catch" in html


# ---------------------------------------------------------------------------
# D3: data.json structure tests
# ---------------------------------------------------------------------------

DATA_JSON_PATH = Path(__file__).parent.parent / "docs" / "data.json"


class TestDataJson:
    def test_file_exists(self):
        assert DATA_JSON_PATH.exists()

    def test_valid_json(self):
        data = json.loads(DATA_JSON_PATH.read_text())
        assert data is not None

    def test_has_generated_at(self):
        data = json.loads(DATA_JSON_PATH.read_text())
        assert "generated_at" in data

    def test_has_repos_list(self):
        data = json.loads(DATA_JSON_PATH.read_text())
        assert isinstance(data["repos"], list)

    def test_has_8_plus_repos(self):
        data = json.loads(DATA_JSON_PATH.read_text())
        assert len(data["repos"]) >= 8

    def test_repo_fields(self):
        data = json.loads(DATA_JSON_PATH.read_text())
        for repo in data["repos"]:
            assert "name" in repo
            assert "url" in repo
            assert "score" in repo
            assert "grade" in repo
            assert "ecosystem" in repo

    def test_stats_present(self):
        data = json.loads(DATA_JSON_PATH.read_text())
        assert "stats" in data
        assert "total" in data["stats"]
        assert "median" in data["stats"]
        assert "top_score" in data["stats"]

    def test_stats_total_matches_repos(self):
        data = json.loads(DATA_JSON_PATH.read_text())
        assert data["stats"]["total"] == len(data["repos"])
