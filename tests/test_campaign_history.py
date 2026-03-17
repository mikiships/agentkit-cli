"""Tests for campaign history DB integration (D3)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentkit_cli.campaign import CampaignResult, PRResult, RepoSpec
from agentkit_cli.history import HistoryDB
from agentkit_cli.main import app

runner = CliRunner()


@pytest.fixture
def tmp_db(tmp_path):
    return tmp_path / "test.db"


def _make_result(campaign_id="cmp001", target="github:pallets"):
    result = CampaignResult(campaign_id=campaign_id, target_spec=target, file="CLAUDE.md")
    result.submitted.append(
        PRResult(
            repo=RepoSpec("pallets", "flask", stars=68000),
            pr_url="https://github.com/pallets/flask/pull/1",
        )
    )
    result.skipped.append(RepoSpec("pallets", "click", stars=15000))
    result.failed.append((RepoSpec("pallets", "jinja"), "fork failed"))
    return result


# ---------------------------------------------------------------------------
# DB schema tests
# ---------------------------------------------------------------------------

def test_campaigns_table_created(tmp_db):
    db = HistoryDB(tmp_db)
    with db._connect() as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='campaigns'"
        ).fetchone()
    assert row is not None


def test_runs_has_campaign_id_column(tmp_db):
    db = HistoryDB(tmp_db)
    with db._connect() as conn:
        info = conn.execute("PRAGMA table_info(runs)").fetchall()
    col_names = [r["name"] for r in info]
    assert "campaign_id" in col_names


# ---------------------------------------------------------------------------
# record_campaign tests
# ---------------------------------------------------------------------------

def test_record_campaign_inserts_row(tmp_db):
    db = HistoryDB(tmp_db)
    result = _make_result()
    db.record_campaign(result)

    rows = db.get_campaigns()
    assert len(rows) == 1
    assert rows[0]["campaign_id"] == "cmp001"
    assert rows[0]["target_spec"] == "github:pallets"
    assert rows[0]["pr_count"] == 1
    assert rows[0]["skip_count"] == 1
    assert rows[0]["fail_count"] == 1
    assert rows[0]["total_repos"] == 3


def test_record_campaign_idempotent(tmp_db):
    db = HistoryDB(tmp_db)
    result = _make_result()
    db.record_campaign(result)
    db.record_campaign(result)  # second call should upsert

    rows = db.get_campaigns()
    assert len(rows) == 1  # still just one row


def test_record_campaign_multiple(tmp_db):
    db = HistoryDB(tmp_db)
    db.record_campaign(_make_result("c1", "github:pallets"))
    db.record_campaign(_make_result("c2", "topic:ai-agents"))

    rows = db.get_campaigns()
    assert len(rows) == 2


# ---------------------------------------------------------------------------
# get_campaigns tests
# ---------------------------------------------------------------------------

def test_get_campaigns_empty(tmp_db):
    db = HistoryDB(tmp_db)
    assert db.get_campaigns() == []


def test_get_campaigns_limit(tmp_db):
    db = HistoryDB(tmp_db)
    for i in range(5):
        db.record_campaign(_make_result(f"c{i}"))
    rows = db.get_campaigns(limit=3)
    assert len(rows) == 3


# ---------------------------------------------------------------------------
# get_campaign_runs tests
# ---------------------------------------------------------------------------

def test_get_campaign_runs_empty(tmp_db):
    db = HistoryDB(tmp_db)
    db.record_campaign(_make_result("c1"))
    runs = db.get_campaign_runs("c1")
    assert runs == []


def test_get_campaign_runs_with_data(tmp_db):
    db = HistoryDB(tmp_db)
    db.record_campaign(_make_result("c1"))
    db.record_run("flask", "agentlint", 85.0, campaign_id="c1")
    runs = db.get_campaign_runs("c1")
    assert len(runs) == 1
    assert runs[0]["project"] == "flask"


# ---------------------------------------------------------------------------
# CLI --campaigns and --campaign-id tests
# ---------------------------------------------------------------------------

def test_history_campaigns_flag_empty(tmp_db):
    result = runner.invoke(app, ["history", "--campaigns", "--db", str(tmp_db)])
    assert result.exit_code == 0
    assert "No campaigns found" in result.output


def test_history_campaigns_flag_with_data(tmp_db):
    db = HistoryDB(tmp_db)
    db.record_campaign(_make_result("abc123"))

    result = runner.invoke(app, ["history", "--campaigns", "--db", str(tmp_db)])
    assert result.exit_code == 0
    assert "abc123" in result.output


def test_history_campaigns_json(tmp_db):
    db = HistoryDB(tmp_db)
    db.record_campaign(_make_result("xyz789"))

    result = runner.invoke(app, ["history", "--campaigns", "--json", "--db", str(tmp_db)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["campaign_id"] == "xyz789"


def test_history_campaign_id_flag(tmp_db):
    db = HistoryDB(tmp_db)
    db.record_campaign(_make_result("cmpXX"))

    result = runner.invoke(app, ["history", "--campaign-id", "cmpXX", "--db", str(tmp_db)])
    assert result.exit_code == 0
    assert "cmpXX" in result.output


def test_history_campaign_id_json(tmp_db):
    db = HistoryDB(tmp_db)
    db.record_campaign(_make_result("cmpYY"))

    result = runner.invoke(app, ["history", "--campaign-id", "cmpYY", "--json", "--db", str(tmp_db)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "campaign" in data
    assert data["campaign"]["campaign_id"] == "cmpYY"
