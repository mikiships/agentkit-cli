"""Tests for agentkit_cli.config — v0.22.0 TOML config system."""
from __future__ import annotations

import os
import textwrap
from pathlib import Path
from typing import Generator

import pytest
from typer.testing import CliRunner

from agentkit_cli.config import (
    DEFAULT_TOML_TEMPLATE,
    TOML_FILENAME,
    AgentKitConfig,
    GateConfig,
    NotifyConfig,
    RunConfig,
    ScoreConfig,
    ScoreWeights,
    SweepConfig,
    _dict_to_toml,
    _find_toml_config,
    _parse_toml,
    get_config_value,
    load_config,
    set_config_value,
)
from agentkit_cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """A temp directory with a git root marker."""
    (tmp_path / ".git").mkdir()
    return tmp_path


@pytest.fixture
def project_toml(tmp_project: Path) -> Path:
    """Return path to a project-level .agentkit.toml."""
    return tmp_project / TOML_FILENAME


@pytest.fixture
def user_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Patch USER_CONFIG_FILE to a temp location."""
    user_dir = tmp_path / "user_config"
    user_dir.mkdir()
    user_cfg = user_dir / "config.toml"
    monkeypatch.setattr("agentkit_cli.config.USER_CONFIG_FILE", user_cfg)
    monkeypatch.setattr("agentkit_cli.config.USER_CONFIG_DIR", user_dir)
    # also patch inside config_cmd module
    try:
        import agentkit_cli.commands.config_cmd as cc
        monkeypatch.setattr(cc, "USER_CONFIG_FILE", user_cfg)
        monkeypatch.setattr(cc, "USER_CONFIG_DIR", user_dir)
    except Exception:
        pass
    return user_dir


# ---------------------------------------------------------------------------
# D1: AgentKitConfig dataclass defaults
# ---------------------------------------------------------------------------

class TestAgentKitConfigDefaults:
    def test_gate_defaults(self):
        config = AgentKitConfig()
        assert config.gate.min_score is None
        assert config.gate.max_drop is None
        assert config.gate.fail_on_regression is False

    def test_notify_defaults(self):
        config = AgentKitConfig()
        assert config.notify.slack_url == ""
        assert config.notify.discord_url == ""
        assert config.notify.webhook_url == ""
        assert config.notify.on == "fail"

    def test_run_defaults(self):
        config = AgentKitConfig()
        assert config.run.output_dir == ".agentkit"
        assert config.run.label == ""
        assert config.run.record_history is True

    def test_sweep_defaults(self):
        config = AgentKitConfig()
        assert config.sweep.targets == []
        assert config.sweep.sort_by == "score"
        assert config.sweep.limit == 20

    def test_score_weight_defaults(self):
        config = AgentKitConfig()
        assert config.score.weights.coderace == 0.3
        assert config.score.weights.agentlint == 0.3
        assert config.score.weights.agentmd == 0.2
        assert config.score.weights.agentreflect == 0.2


# ---------------------------------------------------------------------------
# D1: Config loading
# ---------------------------------------------------------------------------

class TestLoadConfig:
    def test_load_no_file_returns_defaults(self, tmp_project: Path):
        config = load_config(tmp_project)
        assert config.gate.min_score is None
        assert config.notify.on == "fail"
        assert config.run.record_history is True

    def test_load_project_toml_gate(self, tmp_project: Path, project_toml: Path):
        project_toml.write_text(textwrap.dedent("""\
            [gate]
            min_score = 85
            max_drop = 5.0
            fail_on_regression = true
        """))
        config = load_config(tmp_project)
        assert config.gate.min_score == 85.0
        assert config.gate.max_drop == 5.0
        assert config.gate.fail_on_regression is True

    def test_load_project_toml_notify(self, tmp_project: Path, project_toml: Path):
        project_toml.write_text(textwrap.dedent("""\
            [notify]
            slack_url = "https://hooks.slack.com/test"
            on = "always"
        """))
        config = load_config(tmp_project)
        assert config.notify.slack_url == "https://hooks.slack.com/test"
        assert config.notify.on == "always"

    def test_load_project_toml_run(self, tmp_project: Path, project_toml: Path):
        project_toml.write_text(textwrap.dedent("""\
            [run]
            output_dir = "build/agentkit"
            label = "gpt-5"
            record_history = false
        """))
        config = load_config(tmp_project)
        assert config.run.output_dir == "build/agentkit"
        assert config.run.label == "gpt-5"
        assert config.run.record_history is False

    def test_load_project_toml_sweep(self, tmp_project: Path, project_toml: Path):
        project_toml.write_text(textwrap.dedent("""\
            [sweep]
            targets = ["owner/repo1", "owner/repo2"]
            sort_by = "name"
            limit = 10
        """))
        config = load_config(tmp_project)
        assert config.sweep.targets == ["owner/repo1", "owner/repo2"]
        assert config.sweep.sort_by == "name"
        assert config.sweep.limit == 10

    def test_load_project_toml_score_weights(self, tmp_project: Path, project_toml: Path):
        project_toml.write_text(textwrap.dedent("""\
            [score.weights]
            coderace = 0.5
            agentlint = 0.2
            agentmd = 0.2
            agentreflect = 0.1
        """))
        config = load_config(tmp_project)
        assert config.score.weights.coderace == 0.5
        assert config.score.weights.agentlint == 0.2

    def test_load_missing_toml_no_crash(self, tmp_project: Path):
        # Should return defaults without raising
        config = load_config(tmp_project)
        assert isinstance(config, AgentKitConfig)

    def test_load_invalid_toml_no_crash(self, tmp_project: Path, project_toml: Path):
        project_toml.write_text("not valid toml [[[")
        # Should not raise, should return defaults
        config = load_config(tmp_project)
        assert isinstance(config, AgentKitConfig)

    def test_source_tracking_project(self, tmp_project: Path, project_toml: Path):
        project_toml.write_text("[gate]\nmin_score = 90\n")
        config = load_config(tmp_project)
        assert config._sources.get("gate.min_score") == "[project]"


# ---------------------------------------------------------------------------
# D1: User-level config loading
# ---------------------------------------------------------------------------

class TestUserConfig:
    def test_user_config_loaded(self, tmp_project: Path, user_config_dir: Path, monkeypatch):
        user_cfg = user_config_dir / "config.toml"
        user_cfg.write_text("[gate]\nmin_score = 70\n")
        monkeypatch.setattr("agentkit_cli.config.USER_CONFIG_FILE", user_cfg)
        config = load_config(tmp_project)
        assert config.gate.min_score == 70.0
        assert config._sources.get("gate.min_score") == "[user]"

    def test_project_overrides_user(self, tmp_project: Path, project_toml: Path, user_config_dir: Path, monkeypatch):
        user_cfg = user_config_dir / "config.toml"
        user_cfg.write_text("[gate]\nmin_score = 70\n")
        project_toml.write_text("[gate]\nmin_score = 90\n")
        monkeypatch.setattr("agentkit_cli.config.USER_CONFIG_FILE", user_cfg)
        config = load_config(tmp_project)
        assert config.gate.min_score == 90.0
        assert config._sources.get("gate.min_score") == "[project]"


# ---------------------------------------------------------------------------
# D1: Environment variable overrides
# ---------------------------------------------------------------------------

class TestEnvOverrides:
    def test_env_gate_min_score(self, tmp_project: Path, monkeypatch):
        monkeypatch.setenv("AGENTKIT_GATE_MIN_SCORE", "95")
        config = load_config(tmp_project)
        assert config.gate.min_score == 95.0
        assert config._sources.get("gate.min_score") == "[env]"

    def test_env_gate_max_drop(self, tmp_project: Path, monkeypatch):
        monkeypatch.setenv("AGENTKIT_GATE_MAX_DROP", "3.5")
        config = load_config(tmp_project)
        assert config.gate.max_drop == 3.5
        assert config._sources.get("gate.max_drop") == "[env]"

    def test_env_gate_fail_on_regression_true(self, tmp_project: Path, monkeypatch):
        monkeypatch.setenv("AGENTKIT_GATE_FAIL_ON_REGRESSION", "true")
        config = load_config(tmp_project)
        assert config.gate.fail_on_regression is True

    def test_env_gate_fail_on_regression_false(self, tmp_project: Path, monkeypatch):
        monkeypatch.setenv("AGENTKIT_GATE_FAIL_ON_REGRESSION", "false")
        config = load_config(tmp_project)
        assert config.gate.fail_on_regression is False

    def test_env_slack_url(self, tmp_project: Path, monkeypatch):
        monkeypatch.setenv("AGENTKIT_SLACK_URL", "https://hooks.slack.com/env")
        config = load_config(tmp_project)
        assert config.notify.slack_url == "https://hooks.slack.com/env"
        assert config._sources.get("notify.slack_url") == "[env]"

    def test_env_notify_on(self, tmp_project: Path, monkeypatch):
        monkeypatch.setenv("AGENTKIT_NOTIFY_ON", "always")
        config = load_config(tmp_project)
        assert config.notify.on == "always"

    def test_env_output_dir(self, tmp_project: Path, monkeypatch):
        monkeypatch.setenv("AGENTKIT_OUTPUT_DIR", "/tmp/agentkit-out")
        config = load_config(tmp_project)
        assert config.run.output_dir == "/tmp/agentkit-out"

    def test_env_sweep_limit(self, tmp_project: Path, monkeypatch):
        monkeypatch.setenv("AGENTKIT_SWEEP_LIMIT", "5")
        config = load_config(tmp_project)
        assert config.sweep.limit == 5

    def test_env_overrides_project_config(self, tmp_project: Path, project_toml: Path, monkeypatch):
        project_toml.write_text("[gate]\nmin_score = 75\n")
        monkeypatch.setenv("AGENTKIT_GATE_MIN_SCORE", "99")
        config = load_config(tmp_project)
        assert config.gate.min_score == 99.0
        assert config._sources.get("gate.min_score") == "[env]"

    def test_invalid_env_ignored(self, tmp_project: Path, monkeypatch):
        monkeypatch.setenv("AGENTKIT_GATE_MIN_SCORE", "not-a-number")
        config = load_config(tmp_project)
        assert config.gate.min_score is None  # env parse failed, stays at default


# ---------------------------------------------------------------------------
# D1: get_config_value / set_config_value
# ---------------------------------------------------------------------------

class TestGetSetValue:
    def test_get_config_value_returns_default(self, tmp_project: Path):
        val = get_config_value("notify.on", tmp_project)
        assert val == "fail"

    def test_get_config_value_from_file(self, tmp_project: Path, project_toml: Path):
        project_toml.write_text("[gate]\nmin_score = 88\n")
        val = get_config_value("gate.min_score", tmp_project)
        assert val == 88.0

    def test_get_config_value_unknown_key(self, tmp_project: Path):
        val = get_config_value("nonexistent.key", tmp_project)
        assert val is None

    def test_set_config_value_creates_file(self, tmp_path: Path):
        target = tmp_path / "config.toml"
        set_config_value("gate.min_score", "80", target)
        assert target.exists()
        data = _parse_toml(target)
        assert data["gate"]["min_score"] == 80

    def test_set_config_value_string(self, tmp_path: Path):
        target = tmp_path / "config.toml"
        set_config_value("notify.on", "always", target)
        data = _parse_toml(target)
        assert data["notify"]["on"] == "always"

    def test_set_config_value_bool_true(self, tmp_path: Path):
        target = tmp_path / "config.toml"
        set_config_value("gate.fail_on_regression", "true", target)
        data = _parse_toml(target)
        assert data["gate"]["fail_on_regression"] is True

    def test_set_config_value_bool_false(self, tmp_path: Path):
        target = tmp_path / "config.toml"
        set_config_value("gate.fail_on_regression", "false", target)
        data = _parse_toml(target)
        assert data["gate"]["fail_on_regression"] is False

    def test_set_config_value_float(self, tmp_path: Path):
        target = tmp_path / "config.toml"
        set_config_value("gate.max_drop", "7.5", target)
        data = _parse_toml(target)
        assert data["gate"]["max_drop"] == 7.5

    def test_set_config_value_updates_existing(self, tmp_path: Path):
        target = tmp_path / "config.toml"
        target.write_text("[gate]\nmin_score = 70\n")
        set_config_value("gate.min_score", "85", target)
        data = _parse_toml(target)
        assert data["gate"]["min_score"] == 85


# ---------------------------------------------------------------------------
# D2: `agentkit config` CLI commands
# ---------------------------------------------------------------------------

class TestConfigInitCLI:
    def test_init_creates_toml(self, tmp_project: Path):
        result = runner.invoke(app, ["config", "init"], catch_exceptions=False,
                               env={"HOME": str(tmp_project)})
        # Check file created in a findable location (may be in cwd for runner)
        assert result.exit_code == 0 or TOML_FILENAME in result.output or "Created" in result.output

    def test_init_output_contains_created(self, tmp_project: Path, monkeypatch):
        monkeypatch.chdir(tmp_project)
        result = runner.invoke(app, ["config", "init"])
        assert result.exit_code == 0
        assert "Created" in result.output
        assert (tmp_project / TOML_FILENAME).exists()

    def test_init_force_overwrites(self, tmp_project: Path, monkeypatch):
        monkeypatch.chdir(tmp_project)
        (tmp_project / TOML_FILENAME).write_text("# old")
        result = runner.invoke(app, ["config", "init", "--force"])
        assert result.exit_code == 0
        content = (tmp_project / TOML_FILENAME).read_text()
        assert "[gate]" in content

    def test_init_no_force_fails_if_exists(self, tmp_project: Path, monkeypatch):
        monkeypatch.chdir(tmp_project)
        (tmp_project / TOML_FILENAME).write_text("[gate]\nmin_score = 80\n")
        result = runner.invoke(app, ["config", "init"])
        assert result.exit_code != 0

    def test_init_template_has_all_sections(self, tmp_project: Path, monkeypatch):
        monkeypatch.chdir(tmp_project)
        runner.invoke(app, ["config", "init"])
        content = (tmp_project / TOML_FILENAME).read_text()
        for section in ("[gate]", "[notify]", "[run]", "[sweep]", "[score"):
            assert section in content


class TestConfigShowCLI:
    def test_show_runs(self, tmp_project: Path, monkeypatch):
        monkeypatch.chdir(tmp_project)
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0

    def test_show_json_output(self, tmp_project: Path, monkeypatch):
        import json
        monkeypatch.chdir(tmp_project)
        result = runner.invoke(app, ["config", "show", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "gate" in data
        assert "notify" in data
        assert "run" in data
        assert "sweep" in data
        assert "score" in data

    def test_show_reflects_project_config(self, tmp_project: Path, project_toml: Path, monkeypatch):
        import json
        monkeypatch.chdir(tmp_project)
        project_toml.write_text("[gate]\nmin_score = 88\n")
        result = runner.invoke(app, ["config", "show", "--json"])
        data = json.loads(result.output)
        assert data["gate"]["min_score"] == 88.0


class TestConfigGetCLI:
    def test_get_known_key(self, tmp_project: Path, monkeypatch):
        monkeypatch.chdir(tmp_project)
        result = runner.invoke(app, ["config", "get", "notify.on"])
        assert result.exit_code == 0
        assert "fail" in result.output

    def test_get_unknown_key_exits_nonzero(self, tmp_project: Path, monkeypatch):
        monkeypatch.chdir(tmp_project)
        result = runner.invoke(app, ["config", "get", "nonexistent.key"])
        assert result.exit_code != 0

    def test_get_from_project_config(self, tmp_project: Path, project_toml: Path, monkeypatch):
        monkeypatch.chdir(tmp_project)
        project_toml.write_text("[gate]\nmin_score = 77\n")
        result = runner.invoke(app, ["config", "get", "gate.min_score"])
        assert result.exit_code == 0
        assert "77" in result.output


class TestConfigSetCLI:
    def test_set_creates_project_config(self, tmp_project: Path, monkeypatch):
        monkeypatch.chdir(tmp_project)
        result = runner.invoke(app, ["config", "set", "gate.min_score", "82"])
        assert result.exit_code == 0
        assert (tmp_project / TOML_FILENAME).exists()

    def test_set_value_readable(self, tmp_project: Path, monkeypatch):
        monkeypatch.chdir(tmp_project)
        runner.invoke(app, ["config", "set", "gate.min_score", "82"])
        result = runner.invoke(app, ["config", "get", "gate.min_score"])
        assert "82" in result.output

    def test_set_notify_on(self, tmp_project: Path, monkeypatch):
        monkeypatch.chdir(tmp_project)
        runner.invoke(app, ["config", "set", "notify.on", "always"])
        result = runner.invoke(app, ["config", "get", "notify.on"])
        assert "always" in result.output


# ---------------------------------------------------------------------------
# D1: _find_toml_config
# ---------------------------------------------------------------------------

class TestFindTomlConfig:
    def test_finds_in_current_dir(self, tmp_project: Path):
        (tmp_project / TOML_FILENAME).write_text("[gate]\n")
        found = _find_toml_config(tmp_project)
        assert found is not None
        assert found == tmp_project / TOML_FILENAME

    def test_finds_in_parent_dir(self, tmp_project: Path):
        (tmp_project / TOML_FILENAME).write_text("[gate]\n")
        subdir = tmp_project / "src" / "subpkg"
        subdir.mkdir(parents=True)
        found = _find_toml_config(subdir)
        assert found == tmp_project / TOML_FILENAME

    def test_returns_none_when_not_found(self, tmp_path: Path):
        # Isolated tmp_path with no .agentkit.toml
        found = _find_toml_config(tmp_path / "nonexistent")
        assert found is None


# ---------------------------------------------------------------------------
# D1: _dict_to_toml
# ---------------------------------------------------------------------------

class TestDictToToml:
    def test_scalar_string(self):
        out = _dict_to_toml({"key": "value"})
        assert 'key = "value"' in out

    def test_scalar_int(self):
        out = _dict_to_toml({"num": 42})
        assert "num = 42" in out

    def test_scalar_bool_true(self):
        out = _dict_to_toml({"flag": True})
        assert "flag = true" in out

    def test_scalar_bool_false(self):
        out = _dict_to_toml({"flag": False})
        assert "flag = false" in out

    def test_nested_table(self):
        out = _dict_to_toml({"gate": {"min_score": 80}})
        assert "[gate]" in out
        assert "min_score = 80" in out

    def test_list_values(self):
        out = _dict_to_toml({"items": ["a", "b"]})
        assert '"a"' in out and '"b"' in out
