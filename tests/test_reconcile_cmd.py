from __future__ import annotations

import json

from typer.testing import CliRunner

from agentkit_cli.main import app
from tests.test_reconcile_engine import _git, _save_observe_and_supervise, _write_launch, _write_observe_result
from tests.test_launch_engine import _make_repo

runner = CliRunner()


def test_reconcile_command_writes_packet_directory_and_json(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Retry this lane.")
    _save_observe_and_supervise(project)

    output_dir = tmp_path / "reconcile-report"
    result = runner.invoke(app, ["reconcile", str(project), "--output-dir", str(output_dir), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads("\n".join(result.output.splitlines()[1:]))
    assert payload["schema_version"] == "agentkit.reconcile.v1"
    assert payload["relaunch_ready_lane_ids"] == ["lane-01"]
    assert (output_dir / "reconcile.md").exists()
    assert (output_dir / "reconcile.json").exists()
    assert (output_dir / "lanes" / "lane-01" / "reconcile.json").exists()


def test_reconcile_command_supports_explicit_launch_path(tmp_path):
    project = _make_repo(tmp_path)
    launch_dir = _write_launch(project, target="generic", single_lane=True)

    result = runner.invoke(app, ["reconcile", str(project), "--launch-path", str(launch_dir / "launch.json"), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["launch_path"].endswith("launch/launch.json")


def test_reconcile_help():
    result = runner.invoke(app, ["reconcile", "--help"])
    assert result.exit_code == 0
    assert "--launch-path" in result.output
    assert "--output-dir" in result.output
