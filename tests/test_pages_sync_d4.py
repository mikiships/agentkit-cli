"""Tests for D4: source field in data.json + docs/index.html community badges."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── source field in data.json ─────────────────────────────────────────────────

def test_pages_refresh_build_data_json_has_source_field():
    """build_data_json adds source='ecosystem' to each entry."""
    from agentkit_cli.commands.pages_refresh import build_data_json

    eco = MagicMock()
    eco.ecosystem = "python"
    entry = MagicMock()
    entry.repo_full_name = "owner/repo"
    entry.score = 75.0
    entry.grade = "B"
    entry.ecosystem = "python"
    eco.entries = [entry]

    result = MagicMock()
    result.ecosystems = [eco]

    data = build_data_json(result)
    assert data["repos"][0]["source"] == "ecosystem"


def test_sync_engine_community_source():
    """SyncEngine sets source='community' for history entries."""
    import tempfile
    from agentkit_cli.pages_sync_engine import SyncEngine
    from agentkit_cli.history import HistoryDB

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        db = HistoryDB(db_path=tmp / "h.db")
        db.record_run("github:owner/repo", "overall", 75.0)
        engine = SyncEngine(db=db, docs_dir=tmp / "docs")
        (tmp / "docs").mkdir()
        rows = engine.read_history()
        entries = engine.build_entries(rows)
        assert entries[0]["source"] == "community"


def test_merge_keeps_ecosystem_source():
    """Ecosystem-source entries keep their source after merge."""
    import tempfile
    from agentkit_cli.pages_sync_engine import SyncEngine
    from agentkit_cli.history import HistoryDB

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        db = HistoryDB(db_path=tmp / "h.db")
        engine = SyncEngine(db=db, docs_dir=tmp / "docs")
        (tmp / "docs").mkdir()

        existing = {
            "repos": [{"name": "a/repo", "url": "", "score": 85.0, "grade": "A", "ecosystem": "python", "source": "ecosystem"}],
            "stats": {},
        }
        community = [{"name": "b/repo", "url": "", "score": 70.0, "grade": "B", "ecosystem": "", "source": "community", "synced_at": ""}]
        merged, _, _ = engine.merge_entries(existing, community)

        sources = {r["name"]: r["source"] for r in merged["repos"]}
        assert sources["a/repo"] == "ecosystem"
        assert sources["b/repo"] == "community"


def test_data_json_source_field_written_by_sync():
    """After sync, data.json entries have source field."""
    import tempfile
    from agentkit_cli.pages_sync_engine import SyncEngine
    from agentkit_cli.history import HistoryDB

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        db = HistoryDB(db_path=tmp / "h.db")
        db.record_run("github:owner/repo", "overall", 75.0)
        docs = tmp / "docs"
        docs.mkdir()
        engine = SyncEngine(db=db, docs_dir=docs)
        engine.sync(push=False)
        data = json.loads((docs / "data.json").read_text())
        assert "source" in data["repos"][0]
        assert data["repos"][0]["source"] == "community"


# ── docs/index.html ───────────────────────────────────────────────────────────

def test_index_html_has_source_badge_css():
    """docs/index.html contains source-badge CSS classes."""
    index = Path(__file__).parent.parent / "docs" / "index.html"
    html = index.read_text(encoding="utf-8")
    assert "source-badge" in html
    assert "source-ecosystem" in html
    assert "source-community" in html


def test_index_html_has_community_scored_stat():
    """docs/index.html has a community-scored-stat element."""
    index = Path(__file__).parent.parent / "docs" / "index.html"
    html = index.read_text(encoding="utf-8")
    assert "community-scored-stat" in html
    assert "Community Scored" in html


def test_index_html_has_repos_scored_stat_id():
    """docs/index.html repos-scored stat has the id attribute."""
    index = Path(__file__).parent.parent / "docs" / "index.html"
    html = index.read_text(encoding="utf-8")
    assert 'id="repos-scored-stat"' in html


def test_fetch_script_renders_source_badge():
    """The JS fetch script includes source-badge rendering logic."""
    from agentkit_cli.commands.pages_refresh import _fetch_script
    script = _fetch_script()
    assert "source-badge" in script
    # Dynamic class built as 'source-' + srcLabel
    assert "'source-'" in script or "source-badge" in script
    assert "community" in script
