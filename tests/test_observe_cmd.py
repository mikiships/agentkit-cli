from __future__ import annotations

import json

from typer.testing import CliRunner

from agentkit_cli.launch import LaunchEngine
from agentkit_cli.main import app
from tests.test_launch_engine import _make_repo, _write_materialize
from tests.test_observe_engine import _write_observe_result

runner = CliRunner()


def _write_launch(project, *, target="codex", overlap=False, single_lane=False):
    _write_materialize(project, target=target, overlap=overlap, single_lane=single_lane)
    launch_dir = project / "launch"
    plan = LaunchEngine().build(project, target=target)
    LaunchEngine().write_directory(plan, launch_dir)
    (project / "launch.json").write_text((launch_dir / "launch.json").read_text(encoding="utf-8"), encoding="utf-8")


def test_observe_command_writes_packet_directory_and_json(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "success", "Done.")
    output_dir = tmp_path / "observe-report"

    result = runner.invoke(app, ["observe", str(project), "--target", "codex", "--output-dir", str(output_dir), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads("\n".join(result.output.splitlines()[1:]))
    assert payload["schema_version"] == "agentkit.observe.v1"
    assert payload["success_lane_ids"] == ["lane-01"]
    assert (output_dir / "observe.md").exists()
    assert (output_dir / "observe.json").exists()
    assert (output_dir / "lanes" / "lane-01" / "observe.json").exists()


def test_observe_command_fails_on_target_mismatch(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="generic", single_lane=True)

    result = runner.invoke(app, ["observe", str(project), "--target", "codex"])

    assert result.exit_code == 2
    assert "does not match saved launch target" in result.output


def test_observe_help():
    result = runner.invoke(app, ["observe", "--help"])
    assert result.exit_code == 0
    assert "--output-dir" in result.output
