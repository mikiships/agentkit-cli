from __future__ import annotations

import json

from typer.testing import CliRunner

from agentkit_cli.main import app
from tests.test_land_engine import _save_land_chain
from tests.test_launch_engine import _make_repo
from tests.test_reconcile_engine import _git, _write_launch, _write_observe_result

runner = CliRunner()


def test_land_command_writes_packet_directory_and_json(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_land_chain(project)

    output_dir = tmp_path / "land-report"
    result = runner.invoke(app, ["land", str(project), "--output-dir", str(output_dir), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads("\n".join(result.output.splitlines()[1:]))
    assert payload["schema_version"] == "agentkit.land.v1"
    assert payload["land_now_lane_ids"] == ["lane-01"]
    assert (output_dir / "land.md").exists()
    assert (output_dir / "land.json").exists()
    assert (output_dir / "lanes" / "lane-01" / "packet.md").exists()


def test_land_command_supports_explicit_closeout_directory(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Retry lane 01.")
    _save_land_chain(project)

    result = runner.invoke(app, ["land", str(project), "--closeout-path", str(project / "closeout"), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["closeout_path"].endswith("closeout/closeout.json")


def test_land_help():
    result = runner.invoke(app, ["land", "--help"])
    assert result.exit_code == 0
    assert "--closeout-path" in result.output
    assert "--packet-dir" in result.output
