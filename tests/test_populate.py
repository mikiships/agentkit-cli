"""Tests for agentkit populate engine and command — v0.84.0."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.populate_engine import PopulateEngine, PopulateResult, PopulateTopicResult, PopulateEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(tmp_path, records=None):
    from agentkit_cli.history import HistoryDB
    db = HistoryDB(db_path=tmp_path / "test.db")
    for rec in (records or []):
        db.record_run(*rec)
    return db


def _make_engine(tmp_path, analyze_fn=None, search_fn=None):
    db = _make_db(tmp_path)
    return PopulateEngine(
        db=db,
        _analyze_fn=analyze_fn or (lambda repo: 75.0),
        _search_fn=search_fn or (lambda topic, limit, lang, token: [
            {"full_name": f"owner/{topic}-repo-{i}"} for i in range(min(limit, 3))
        ]),
    )


# ---------------------------------------------------------------------------
# Unit tests for PopulateEngine
# ---------------------------------------------------------------------------

class TestPopulateEngineBasic:
    def test_populate_returns_result(self, tmp_path):
        engine = _make_engine(tmp_path)
        result = engine.populate(topics=["python"], limit=3, quiet=True)
        assert isinstance(result, PopulateResult)
        assert result.topics == ["python"]

    def test_populate_scores_repos(self, tmp_path):
        engine = _make_engine(tmp_path)
        result = engine.populate(topics=["python"], limit=3, quiet=True)
        assert result.total_scored == 3

    def test_populate_dry_run_skips_scoring(self, tmp_path):
        scored = []
        def track_analyze(repo):
            scored.append(repo)
            return 70.0
        engine = _make_engine(tmp_path, analyze_fn=track_analyze)
        result = engine.populate(topics=["python"], limit=3, dry_run=True, quiet=True)
        assert len(scored) == 0
        assert result.total_skipped == 3

    def test_populate_force_refresh_rescores(self, tmp_path):
        db = _make_db(tmp_path)
        # Pre-populate fresh entry
        db.record_run(project="owner/python-repo-0", tool="agentkit_populate", score=60.0)
        calls = []
        def track_analyze(repo):
            calls.append(repo)
            return 80.0
        engine = PopulateEngine(
            db=db,
            _analyze_fn=track_analyze,
            _search_fn=lambda topic, limit, lang, token: [{"full_name": "owner/python-repo-0"}],
        )
        result = engine.populate(topics=["python"], limit=1, force_refresh=True, quiet=True)
        assert "owner/python-repo-0" in calls

    def test_populate_skips_fresh_without_force(self, tmp_path):
        db = _make_db(tmp_path)
        db.record_run(project="owner/python-repo-0", tool="agentkit_populate", score=60.0)
        calls = []
        def track_analyze(repo):
            calls.append(repo)
            return 80.0
        engine = PopulateEngine(
            db=db,
            _analyze_fn=track_analyze,
            _search_fn=lambda topic, limit, lang, token: [{"full_name": "owner/python-repo-0"}],
        )
        result = engine.populate(topics=["python"], limit=1, quiet=True)
        assert "owner/python-repo-0" not in calls
        assert result.total_skipped == 1

    def test_populate_multiple_topics(self, tmp_path):
        engine = _make_engine(tmp_path)
        result = engine.populate(topics=["python", "rust"], limit=2, quiet=True)
        assert len(result.topic_results) == 2
        assert result.total_scored == 4  # 2 repos × 2 topics

    def test_populate_stores_to_db(self, tmp_path):
        db = _make_db(tmp_path)
        engine = PopulateEngine(
            db=db,
            _analyze_fn=lambda repo: 85.0,
            _search_fn=lambda topic, limit, lang, token: [{"full_name": "owner/my-repo"}],
        )
        engine.populate(topics=["python"], limit=1, quiet=True)
        history = db.get_history(project="owner/my-repo")
        assert len(history) > 0
        assert history[0]["score"] == 85.0

    def test_populate_topic_result_avg_score(self, tmp_path):
        engine = PopulateEngine(
            db=_make_db(tmp_path),
            _analyze_fn=lambda repo: 80.0,
            _search_fn=lambda topic, limit, lang, token: [
                {"full_name": "a/b"}, {"full_name": "c/d"}
            ],
        )
        result = engine.populate(topics=["python"], limit=2, quiet=True)
        tr = result.topic_results[0]
        assert tr.avg_score == 80.0

    def test_populate_progress_callback_called(self, tmp_path):
        calls = []
        engine = _make_engine(tmp_path)
        engine.populate(
            topics=["python"],
            limit=2,
            quiet=True,
            progress_callback=lambda repo, curr, total: calls.append((repo, curr, total)),
        )
        assert len(calls) == 2
        assert calls[0][1] == 1  # current starts at 1

    def test_populate_handles_search_error(self, tmp_path):
        def failing_search(topic, limit, lang, token):
            raise RuntimeError("Network error")
        engine = PopulateEngine(
            db=_make_db(tmp_path),
            _analyze_fn=lambda repo: 70.0,
            _search_fn=failing_search,
        )
        result = engine.populate(topics=["python"], limit=5, quiet=True)
        assert result.total_scored == 0

    def test_populate_to_dict(self, tmp_path):
        engine = _make_engine(tmp_path)
        result = engine.populate(topics=["python"], limit=2, quiet=True)
        d = result.to_dict()
        assert "topics" in d
        assert "total_scored" in d
        assert "topic_results" in d

    def test_populate_entry_skipped_dry_run(self, tmp_path):
        engine = _make_engine(tmp_path)
        result = engine.populate(topics=["python"], limit=1, dry_run=True, quiet=True)
        entry = result.topic_results[0].entries[0]
        assert entry.skipped
        assert entry.skip_reason == "dry_run"

    def test_populate_default_topics(self, tmp_path):
        engine = _make_engine(tmp_path)
        result = engine.populate(quiet=True)
        assert "python" in result.topics
        assert "typescript" in result.topics


# ---------------------------------------------------------------------------
# Tests for populate_command
# ---------------------------------------------------------------------------

class TestPopulateCommand:
    def _engine(self, tmp_path):
        return _make_engine(tmp_path)

    def test_populate_command_returns_summary(self, tmp_path):
        from agentkit_cli.commands.populate_cmd import populate_command
        engine = self._engine(tmp_path)
        summary = populate_command(topics="python", limit=2, quiet=True, _engine=engine)
        assert summary is not None
        assert "topic_results" in summary

    def test_populate_command_json_output(self, tmp_path, capsys):
        from agentkit_cli.commands.populate_cmd import populate_command
        engine = self._engine(tmp_path)
        populate_command(topics="python", limit=2, quiet=True, json_output=True, _engine=engine)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "topics" in data
