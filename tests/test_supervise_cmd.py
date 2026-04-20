from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app
from tests.test_supervise_engine import _make_repo, _write_launch

runner = CliRunner()


def test_supervise_command_writes_packet_directory(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)
    output_dir = tmp_path / "supervise-report"

    result = runner.invoke(app, ["supervise", str(project), "--output-dir", str(output_dir), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads("\n".join(result.output.splitlines()[1:]))
    assert payload["schema_version"] == "agentkit.supervise.v1"
    assert payload["waiting_lane_ids"] == ["lane-02"]
    assert (output_dir / "supervise.md").exists()
    assert (output_dir / "supervise.json").exists()
    assert (output_dir / "lanes" / "lane-01" / "supervise.json").exists()


def test_supervise_command_supports_explicit_launch_path(tmp_path):
    project = _make_repo(tmp_path)
    launch_dir = _write_launch(project, target="generic", single_lane=True)

    result = runner.invoke(app, ["supervise", str(project), "--launch-path", str(launch_dir / "launch.json"), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["launch_path"].endswith("launch/launch.json")


def test_supervise_help():
    result = runner.invoke(app, ["supervise", "--help"])
    assert result.exit_code == 0
    assert "--launch-path" in result.output
    assert "--output-dir" in result.output
