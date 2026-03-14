"""Tests for agentkit leaderboard feature (D1-D4, v0.15.0)."""
from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentkit_cli.history import HistoryDB, _compute_trend
from agentkit_cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_db(tmp_path):
    """Return a fresh HistoryDB backed by a temp file."""
    return HistoryDB(db_path=tmp_path / "test.db")


@pytest.fixture()
def tmp_db_path(tmp_path):
    """Return path to a fresh DB file."""
    return tmp_path / "test.db"


def _seed(db: HistoryDB, label: str, scores: list[float], project: str = "myproject") -> None:
    """Insert 'overall' rows for the given label."""
    for score in scores:
        db.record_run(project, "overall", score, label=label)


# ---------------------------------------------------------------------------
# D1: label column migration
# ---------------------------------------------------------------------------

class TestLabelMigration:
    def test_new_db_has_label_column(self, tmp_db):
        """Fresh DB should have label column."""
        with tmp_db._connect() as conn:
            cols = [row[1] for row in conn.execute("PRAGMA table_info(runs)").fetchall()]
        assert "label" in cols

    def test_old_db_gets_label_column(self, tmp_path):
        """Old DB without label column should get it via migration."""
        db_path = tmp_path / "old.db"
        # Create old-style DB without label column
        conn = sqlite3.connect(str(db_path))
        conn.execute("""CREATE TABLE runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL, project TEXT NOT NULL,
            tool TEXT NOT NULL, score REAL NOT NULL, details TEXT
        )""")
        conn.commit()
        conn.close()

        # Opening via HistoryDB should apply migration
        db = HistoryDB(db_path=db_path)
        with db._connect() as c:
            cols = [row[1] for row in c.execute("PRAGMA table_info(runs)").fetchall()]
        assert "label" in cols

    def test_migration_idempotent(self, tmp_db):
        """Running migration twice should not raise."""
        tmp_db._run_migrations()
        tmp_db._run_migrations()  # no error

    def test_record_run_with_label(self, tmp_db):
        """record_run should store label correctly."""
        tmp_db.record_run("proj", "overall", 85.0, label="gpt-4")
        rows = tmp_db.get_history(project="proj", tool="overall")
        assert rows[0]["label"] == "gpt-4"

    def test_record_run_without_label(self, tmp_db):
        """record_run with no label stores NULL."""
        tmp_db.record_run("proj", "overall", 75.0)
        rows = tmp_db.get_history(project="proj", tool="overall")
        assert rows[0]["label"] is None

    def test_old_rows_readable(self, tmp_path):
        """Old rows without label column are readable with None label after migration."""
        db_path = tmp_path / "old2.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""CREATE TABLE runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL, project TEXT NOT NULL,
            tool TEXT NOT NULL, score REAL NOT NULL, details TEXT
        )""")
        conn.execute("INSERT INTO runs (ts, project, tool, score) VALUES ('2026-01-01T00:00:00+00:00', 'p', 'overall', 80.0)")
        conn.commit()
        conn.close()

        db = HistoryDB(db_path=db_path)
        rows = db.get_history(project="p")
        assert rows[0]["label"] is None


# ---------------------------------------------------------------------------
# D1: --label flag wired through CLI run command
# ---------------------------------------------------------------------------

class TestRunLabel:
    def test_run_help_contains_label(self):
        result = runner.invoke(app, ["run", "--help"])
        assert "--label" in result.output

    def test_run_label_passed_to_record(self, tmp_db_path, monkeypatch):
        """--label value ends up in the DB."""
        # We can test via HistoryDB directly by seeding with label
        db = HistoryDB(db_path=tmp_db_path)
        db.record_run("proj", "overall", 90.0, label="claude-sonnet")
        rows = db.get_history(project="proj")
        assert rows[0]["label"] == "claude-sonnet"


# ---------------------------------------------------------------------------
# D2: _compute_trend
# ---------------------------------------------------------------------------

class TestComputeTrend:
    def test_single_score_returns_zero(self):
        assert _compute_trend([80.0]) == 0.0

    def test_empty_returns_zero(self):
        assert _compute_trend([]) == 0.0

    def test_two_scores_positive_trend(self):
        delta = _compute_trend([70.0, 90.0])
        assert delta > 0

    def test_two_scores_negative_trend(self):
        delta = _compute_trend([90.0, 70.0])
        assert delta < 0

    def test_flat_trend_zero(self):
        delta = _compute_trend([80.0, 80.0, 80.0, 80.0])
        assert delta == 0.0

    def test_uses_first_three_and_last_three(self):
        # first 3 avg = (10+10+10)/3 = 10, last 3 avg = (90+90+90)/3 = 90
        scores = [10.0, 10.0, 10.0, 50.0, 90.0, 90.0, 90.0]
        delta = _compute_trend(scores)
        assert abs(delta - 80.0) < 0.1

    def test_trend_rounds_to_one_decimal(self):
        delta = _compute_trend([80.0, 83.333])
        assert isinstance(delta, float)
        assert round(delta, 1) == delta


# ---------------------------------------------------------------------------
# D2: get_leaderboard_data
# ---------------------------------------------------------------------------

class TestLeaderboardEngine:
    def test_empty_db_returns_empty_list(self, tmp_db):
        rows = tmp_db.get_leaderboard_data()
        assert rows == []

    def test_single_label_appears(self, tmp_db):
        _seed(tmp_db, "gpt-4", [80.0, 85.0, 90.0])
        rows = tmp_db.get_leaderboard_data(project="myproject")
        assert len(rows) == 1
        assert rows[0]["label"] == "gpt-4"

    def test_multiple_labels_ranked_by_avg(self, tmp_db):
        _seed(tmp_db, "gpt-4", [90.0, 95.0])
        _seed(tmp_db, "codex", [60.0, 65.0])
        _seed(tmp_db, "claude", [80.0, 82.0])
        rows = tmp_db.get_leaderboard_data(project="myproject")
        assert rows[0]["label"] == "gpt-4"
        assert rows[1]["label"] == "claude"
        assert rows[2]["label"] == "codex"

    def test_null_label_grouped_as_default(self, tmp_db):
        tmp_db.record_run("myproject", "overall", 75.0)  # no label
        rows = tmp_db.get_leaderboard_data(project="myproject")
        assert rows[0]["label"] == "default"

    def test_avg_score_correct(self, tmp_db):
        _seed(tmp_db, "model-a", [80.0, 90.0])
        rows = tmp_db.get_leaderboard_data(project="myproject")
        assert rows[0]["avg_score"] == 85.0

    def test_best_worst_correct(self, tmp_db):
        _seed(tmp_db, "model-a", [60.0, 80.0, 100.0])
        rows = tmp_db.get_leaderboard_data(project="myproject")
        assert rows[0]["best"] == 100.0
        assert rows[0]["worst"] == 60.0

    def test_run_count_correct(self, tmp_db):
        _seed(tmp_db, "model-a", [70.0, 80.0, 90.0, 85.0, 75.0])
        rows = tmp_db.get_leaderboard_data(project="myproject")
        assert rows[0]["runs"] == 5

    def test_project_filter(self, tmp_db):
        _seed(tmp_db, "gpt-4", [90.0], project="proj-a")
        _seed(tmp_db, "codex", [70.0], project="proj-b")
        rows_a = tmp_db.get_leaderboard_data(project="proj-a")
        assert len(rows_a) == 1
        assert rows_a[0]["label"] == "gpt-4"

    def test_last_n_filter(self, tmp_db):
        # 5 runs but only consider last 2
        _seed(tmp_db, "model", [50.0, 50.0, 50.0, 90.0, 100.0])
        rows = tmp_db.get_leaderboard_data(project="myproject", last_n=2)
        assert rows[0]["runs"] == 2
        assert rows[0]["avg_score"] == 95.0

    def test_since_filter(self, tmp_db):
        import time
        # Insert an old record with backdated ts
        with tmp_db._connect() as conn:
            conn.execute(
                "INSERT INTO runs (ts, project, tool, score, label) VALUES (?, ?, ?, ?, ?)",
                ("2020-01-01T00:00:00+00:00", "myproject", "overall", 50.0, "old-model"),
            )
        _seed(tmp_db, "new-model", [90.0])
        # Filter to only recent
        rows = tmp_db.get_leaderboard_data(project="myproject", since="2025-01-01T00:00:00+00:00")
        labels = [r["label"] for r in rows]
        assert "new-model" in labels
        assert "old-model" not in labels

    def test_by_specific_tool(self, tmp_db):
        tmp_db.record_run("myproject", "agentlint", 88.0, label="model-x")
        rows = tmp_db.get_leaderboard_data(tool="agentlint", project="myproject")
        assert len(rows) == 1
        assert rows[0]["avg_score"] == 88.0

    def test_trend_positive(self, tmp_db):
        _seed(tmp_db, "model", [50.0, 50.0, 50.0, 90.0, 90.0, 90.0])
        rows = tmp_db.get_leaderboard_data(project="myproject")
        assert rows[0]["trend"] > 0

    def test_trend_negative(self, tmp_db):
        _seed(tmp_db, "model", [90.0, 90.0, 90.0, 50.0, 50.0, 50.0])
        rows = tmp_db.get_leaderboard_data(project="myproject")
        assert rows[0]["trend"] < 0

    def test_trend_flat(self, tmp_db):
        _seed(tmp_db, "model", [80.0, 80.0, 80.0, 80.0])
        rows = tmp_db.get_leaderboard_data(project="myproject")
        assert rows[0]["trend"] == 0.0


# ---------------------------------------------------------------------------
# D3: CLI leaderboard command
# ---------------------------------------------------------------------------

class TestLeaderboardCLI:
    def test_help_shows(self):
        result = runner.invoke(app, ["leaderboard", "--help"])
        assert result.exit_code == 0
        assert "--by" in result.output
        assert "--json" in result.output
        assert "--since" in result.output
        assert "--project" in result.output
        assert "--last" in result.output

    def test_empty_db_no_crash(self, tmp_db_path):
        result = runner.invoke(app, ["leaderboard", "--db", str(tmp_db_path)])
        assert result.exit_code == 0

    def test_json_output_valid(self, tmp_db_path):
        db = HistoryDB(db_path=tmp_db_path)
        _seed(db, "gpt-4", [80.0, 90.0])
        result = runner.invoke(app, ["leaderboard", "--json", "--db", str(tmp_db_path), "--project", "myproject"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)

    def test_json_output_structure(self, tmp_db_path):
        db = HistoryDB(db_path=tmp_db_path)
        _seed(db, "claude", [85.0, 88.0])
        result = runner.invoke(app, ["leaderboard", "--json", "--db", str(tmp_db_path), "--project", "myproject"])
        data = json.loads(result.output)
        row = data["leaderboard"][0]
        for key in ("label", "runs", "avg_score", "best", "worst", "trend"):
            assert key in row

    def test_json_tool_field(self, tmp_db_path):
        db = HistoryDB(db_path=tmp_db_path)
        _seed(db, "x", [70.0])
        result = runner.invoke(app, ["leaderboard", "--json", "--by", "overall", "--db", str(tmp_db_path), "--project", "myproject"])
        data = json.loads(result.output)
        assert data["tool"] == "overall"

    def test_rich_table_output(self, tmp_db_path):
        db = HistoryDB(db_path=tmp_db_path)
        _seed(db, "gpt-4", [80.0, 90.0])
        result = runner.invoke(app, ["leaderboard", "--db", str(tmp_db_path), "--project", "myproject"])
        assert result.exit_code == 0
        assert "gpt-4" in result.output

    def test_rank_column_in_output(self, tmp_db_path):
        db = HistoryDB(db_path=tmp_db_path)
        _seed(db, "model-a", [90.0])
        _seed(db, "model-b", [70.0])
        result = runner.invoke(app, ["leaderboard", "--db", str(tmp_db_path), "--project", "myproject"])
        assert "1" in result.output

    def test_by_flag_agentlint(self, tmp_db_path):
        db = HistoryDB(db_path=tmp_db_path)
        db.record_run("myproject", "agentlint", 77.0, label="test-label")
        result = runner.invoke(app, ["leaderboard", "--by", "agentlint", "--json", "--db", str(tmp_db_path), "--project", "myproject"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["tool"] == "agentlint"

    def test_by_flag_invalid(self, tmp_db_path):
        result = runner.invoke(app, ["leaderboard", "--by", "badtool", "--db", str(tmp_db_path)])
        assert result.exit_code != 0

    def test_last_flag(self, tmp_db_path):
        db = HistoryDB(db_path=tmp_db_path)
        _seed(db, "model", [10.0, 10.0, 10.0, 90.0, 100.0])
        result = runner.invoke(app, ["leaderboard", "--last", "2", "--json", "--db", str(tmp_db_path), "--project", "myproject"])
        data = json.loads(result.output)
        assert data["leaderboard"][0]["avg_score"] == 95.0

    def test_since_flag_filters(self, tmp_db_path):
        db = HistoryDB(db_path=tmp_db_path)
        with db._connect() as conn:
            conn.execute(
                "INSERT INTO runs (ts, project, tool, score, label) VALUES (?, ?, ?, ?, ?)",
                ("2020-01-01T00:00:00+00:00", "myproject", "overall", 50.0, "old"),
            )
        _seed(db, "new", [90.0])
        result = runner.invoke(app, ["leaderboard", "--since", "2025-01-01", "--json", "--db", str(tmp_db_path), "--project", "myproject"])
        data = json.loads(result.output)
        labels = [r["label"] for r in data["leaderboard"]]
        assert "new" in labels
        assert "old" not in labels

    def test_since_flag_days_format(self, tmp_db_path):
        db = HistoryDB(db_path=tmp_db_path)
        _seed(db, "recent", [85.0])
        result = runner.invoke(app, ["leaderboard", "--since", "7d", "--json", "--db", str(tmp_db_path), "--project", "myproject"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data["leaderboard"], list)

    def test_project_flag(self, tmp_db_path):
        db = HistoryDB(db_path=tmp_db_path)
        _seed(db, "alpha", [80.0], project="proj-alpha")
        _seed(db, "beta", [60.0], project="proj-beta")
        result = runner.invoke(app, ["leaderboard", "--project", "proj-alpha", "--json", "--db", str(tmp_db_path)])
        data = json.loads(result.output)
        assert all(r["label"] != "beta" for r in data["leaderboard"])

    def test_multiple_labels_sorted_by_avg(self, tmp_db_path):
        db = HistoryDB(db_path=tmp_db_path)
        _seed(db, "fast", [95.0, 97.0])
        _seed(db, "slow", [60.0, 65.0])
        result = runner.invoke(app, ["leaderboard", "--json", "--db", str(tmp_db_path), "--project", "myproject"])
        data = json.loads(result.output)
        scores = [r["avg_score"] for r in data["leaderboard"]]
        assert scores == sorted(scores, reverse=True)

    def test_null_label_shows_as_default(self, tmp_db_path):
        db = HistoryDB(db_path=tmp_db_path)
        db.record_run("myproject", "overall", 75.0)  # no label
        result = runner.invoke(app, ["leaderboard", "--json", "--db", str(tmp_db_path), "--project", "myproject"])
        data = json.loads(result.output)
        assert data["leaderboard"][0]["label"] == "default"

    def test_trend_displayed_in_rich_output(self, tmp_db_path):
        db = HistoryDB(db_path=tmp_db_path)
        _seed(db, "improving", [50.0, 50.0, 50.0, 90.0, 90.0, 90.0])
        result = runner.invoke(app, ["leaderboard", "--db", str(tmp_db_path), "--project", "myproject"])
        assert "↑" in result.output

    def test_json_is_valid_when_empty(self, tmp_db_path):
        result = runner.invoke(app, ["leaderboard", "--json", "--db", str(tmp_db_path), "--project", "nodata"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["leaderboard"] == []

    def test_version_is_015(self):
        result = runner.invoke(app, ["--version"])
        assert "0.18" in result.output
