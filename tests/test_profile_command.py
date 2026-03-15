"""Tests for agentkit profile CLI commands — D2."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.config import TOML_FILENAME, _parse_toml

runner = CliRunner()


@pytest.fixture
def tmp_project(tmp_path):
    (tmp_path / ".git").mkdir()
    return tmp_path


@pytest.fixture
def user_profiles_dir(tmp_path, monkeypatch):
    d = tmp_path / "profiles"
    d.mkdir()
    monkeypatch.setattr("agentkit_cli.profiles.USER_PROFILES_DIR", d)
    return d


# ---------------------------------------------------------------------------
# agentkit profile list
# ---------------------------------------------------------------------------

class TestProfileList:
    def test_list_exits_zero(self):
        result = runner.invoke(app, ["profile", "list"])
        assert result.exit_code == 0

    def test_list_shows_strict(self):
        result = runner.invoke(app, ["profile", "list"])
        assert "strict" in result.output

    def test_list_shows_balanced(self):
        result = runner.invoke(app, ["profile", "list"])
        assert "balanced" in result.output

    def test_list_shows_minimal(self):
        result = runner.invoke(app, ["profile", "list"])
        assert "minimal" in result.output

    def test_list_shows_table_headers(self):
        result = runner.invoke(app, ["profile", "list"])
        assert "Name" in result.output

    def test_list_shows_built_in_source(self):
        result = runner.invoke(app, ["profile", "list"])
        assert "built-in" in result.output

    def test_list_shows_user_profile(self, user_profiles_dir):
        toml = user_profiles_dir / "myp.toml"
        toml.write_text('name = "myp"\ndescription = "test"\n[gate]\nmin_score = 60.0\n')
        result = runner.invoke(app, ["profile", "list"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# agentkit profile show
# ---------------------------------------------------------------------------

class TestProfileShow:
    def test_show_strict(self):
        result = runner.invoke(app, ["profile", "show", "strict"])
        assert result.exit_code == 0
        assert "strict" in result.output

    def test_show_displays_min_score(self):
        result = runner.invoke(app, ["profile", "show", "strict"])
        assert "85.0" in result.output

    def test_show_displays_max_drop(self):
        result = runner.invoke(app, ["profile", "show", "strict"])
        assert "3.0" in result.output

    def test_show_unknown_profile_exits_1(self):
        result = runner.invoke(app, ["profile", "show", "nonexistent"])
        assert result.exit_code == 1

    def test_show_case_insensitive(self):
        result = runner.invoke(app, ["profile", "show", "STRICT"])
        assert result.exit_code == 0

    def test_show_balanced(self):
        result = runner.invoke(app, ["profile", "show", "balanced"])
        assert result.exit_code == 0
        assert "70.0" in result.output


# ---------------------------------------------------------------------------
# agentkit profile create
# ---------------------------------------------------------------------------

class TestProfileCreate:
    def test_create_basic(self, user_profiles_dir):
        result = runner.invoke(app, ["profile", "create", "myprofile"])
        assert result.exit_code == 0
        assert "Created" in result.output

    def test_create_from_base(self, user_profiles_dir):
        result = runner.invoke(app, ["profile", "create", "mystrict", "--from", "strict"])
        assert result.exit_code == 0

    def test_create_unknown_base_exits_1(self, user_profiles_dir):
        result = runner.invoke(app, ["profile", "create", "x", "--from", "nonexistent"])
        assert result.exit_code == 1

    def test_create_writes_toml_file(self, user_profiles_dir):
        runner.invoke(app, ["profile", "create", "testprofile"])
        assert (user_profiles_dir / "testprofile.toml").exists()


# ---------------------------------------------------------------------------
# agentkit profile use
# ---------------------------------------------------------------------------

class TestProfileUse:
    def test_use_strict_exits_zero(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        result = runner.invoke(app, ["profile", "use", "strict"])
        assert result.exit_code == 0

    def test_use_writes_to_toml(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        runner.invoke(app, ["profile", "use", "balanced"])
        toml_path = tmp_project / TOML_FILENAME
        assert toml_path.exists()
        data = _parse_toml(toml_path)
        assert data.get("profile", {}).get("active") == "balanced"

    def test_use_unknown_profile_exits_1(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        result = runner.invoke(app, ["profile", "use", "nonexistent"])
        assert result.exit_code == 1

    def test_use_roundtrip(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        runner.invoke(app, ["profile", "use", "strict"])
        data = _parse_toml(tmp_project / TOML_FILENAME)
        assert data["profile"]["active"] == "strict"


# ---------------------------------------------------------------------------
# agentkit profile export
# ---------------------------------------------------------------------------

class TestProfileExport:
    def test_export_toml_default(self):
        result = runner.invoke(app, ["profile", "export", "strict"])
        assert result.exit_code == 0
        assert "strict" in result.output

    def test_export_json(self):
        result = runner.invoke(app, ["profile", "export", "strict", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "strict"
        assert data["gate"]["min_score"] == 85.0

    def test_export_unknown_exits_1(self):
        result = runner.invoke(app, ["profile", "export", "nonexistent"])
        assert result.exit_code == 1

    def test_export_json_has_all_sections(self):
        result = runner.invoke(app, ["profile", "export", "balanced", "--format", "json"])
        data = json.loads(result.output)
        assert "gate" in data
        assert "notify" in data
        assert "run" in data
        assert "sweep" in data
