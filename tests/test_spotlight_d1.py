"""Tests for SpotlightEngine core + SpotlightResult (D1 — ≥12 tests)."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.commands.spotlight_cmd import SpotlightEngine, SpotlightResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(**kwargs) -> SpotlightResult:
    defaults = dict(
        repo="acme/cool-agent",
        score=82.5,
        grade="B",
        top_findings=["[agentlint] Missing AGENTS.md"],
        run_date=datetime.now(timezone.utc).isoformat(),
    )
    defaults.update(kwargs)
    return SpotlightResult(**defaults)


FAKE_REPOS = [
    {"full_name": "acme/cool-agent", "description": "A test repo", "stars": 1200, "language": "Python", "url": "https://github.com/acme/cool-agent"},
    {"full_name": "beta/llm-lib", "description": "LLM lib", "stars": 800, "language": "TypeScript", "url": "https://github.com/beta/llm-lib"},
]


# ---------------------------------------------------------------------------
# D1: SpotlightResult dataclass
# ---------------------------------------------------------------------------

class TestSpotlightResult:
    def test_to_dict_contains_required_keys(self):
        r = _make_result()
        d = r.to_dict()
        assert "repo" in d
        assert "score" in d
        assert "grade" in d
        assert "top_findings" in d
        assert "run_date" in d

    def test_to_dict_optional_fields_present(self):
        r = _make_result(redteam_resistance=72.0, cert_id="abcd1234", share_url="https://x.example.com")
        d = r.to_dict()
        assert d["redteam_resistance"] == 72.0
        assert d["cert_id"] == "abcd1234"
        assert d["share_url"] == "https://x.example.com"

    def test_to_dict_none_optionals(self):
        r = _make_result()
        d = r.to_dict()
        assert d["redteam_resistance"] is None
        assert d["cert_id"] is None
        assert d["share_url"] is None

    def test_grade_values(self):
        for grade in ("A", "B", "C", "D", "F"):
            r = _make_result(grade=grade)
            assert r.grade == grade

    def test_top_findings_list(self):
        findings = ["finding1", "finding2", "finding3"]
        r = _make_result(top_findings=findings)
        assert len(r.top_findings) == 3

    def test_run_date_is_string(self):
        r = _make_result()
        assert isinstance(r.run_date, str)

    def test_repo_metadata_defaults(self):
        r = SpotlightResult(repo="x/y", score=70.0, grade="C", top_findings=[], run_date="2026-01-01T00:00:00+00:00")
        assert r.repo_stars == 0
        assert r.repo_language == ""
        assert r.repo_description == ""


# ---------------------------------------------------------------------------
# D1: SpotlightEngine.select_candidate
# ---------------------------------------------------------------------------

class TestSpotlightEngineSelectCandidate:
    def test_returns_first_unspotlighted_repo(self):
        engine = SpotlightEngine()
        with patch("agentkit_cli.commands.spotlight_cmd.fetch_trending", return_value=FAKE_REPOS):
            with patch.object(engine, "_already_spotlighted", return_value=False):
                result = engine.select_candidate()
        assert result is not None
        assert result["full_name"] == "acme/cool-agent"

    def test_skips_already_spotlighted(self):
        engine = SpotlightEngine()
        call_count = {"n": 0}

        def _already(full_name):
            # First repo is spotlighted, second is not
            call_count["n"] += 1
            return full_name == "acme/cool-agent"

        with patch("agentkit_cli.commands.spotlight_cmd.fetch_trending", return_value=FAKE_REPOS):
            with patch.object(engine, "_already_spotlighted", side_effect=_already):
                result = engine.select_candidate()
        assert result["full_name"] == "beta/llm-lib"

    def test_falls_back_to_popular_on_empty_trending(self):
        engine = SpotlightEngine()
        with patch("agentkit_cli.commands.spotlight_cmd.fetch_trending", return_value=[]):
            with patch("agentkit_cli.commands.spotlight_cmd.fetch_popular", return_value=FAKE_REPOS):
                with patch.object(engine, "_already_spotlighted", return_value=False):
                    result = engine.select_candidate()
        assert result is not None

    def test_returns_first_when_all_spotlighted(self):
        engine = SpotlightEngine()
        with patch("agentkit_cli.commands.spotlight_cmd.fetch_trending", return_value=FAKE_REPOS):
            with patch.object(engine, "_already_spotlighted", return_value=True):
                result = engine.select_candidate()
        assert result == FAKE_REPOS[0]

    def test_returns_none_on_exception(self):
        engine = SpotlightEngine()
        with patch("agentkit_cli.commands.spotlight_cmd.fetch_trending", side_effect=Exception("network")):
            with patch("agentkit_cli.commands.spotlight_cmd.fetch_popular", return_value=[]):
                result = engine.select_candidate()
        assert result is None

    def test_topic_filter_passed_to_fetch(self):
        engine = SpotlightEngine()
        with patch("agentkit_cli.commands.spotlight_cmd.fetch_trending", return_value=FAKE_REPOS) as mock_ft:
            with patch.object(engine, "_already_spotlighted", return_value=False):
                engine.select_candidate(topic="llm")
        mock_ft.assert_called_once()
        call_kwargs = mock_ft.call_args[1]
        assert call_kwargs.get("topic") == "llm"


# ---------------------------------------------------------------------------
# D1: SpotlightEngine._score_to_grade
# ---------------------------------------------------------------------------

class TestScoreToGrade:
    def test_grade_boundaries(self):
        engine = SpotlightEngine()
        assert engine._score_to_grade(95) == "A"
        assert engine._score_to_grade(85) == "B"
        assert engine._score_to_grade(75) == "C"
        assert engine._score_to_grade(65) == "D"
        assert engine._score_to_grade(50) == "F"
        assert engine._score_to_grade(None) is None

    def test_grade_at_exact_thresholds(self):
        engine = SpotlightEngine()
        assert engine._score_to_grade(90) == "A"
        assert engine._score_to_grade(80) == "B"
        assert engine._score_to_grade(70) == "C"
        assert engine._score_to_grade(60) == "D"
