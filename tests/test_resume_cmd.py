from __future__ import annotations

import json

from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.observe import ObserveEngine
from agentkit_cli.reconcile import ReconcileEngine
from agentkit_cli.supervise import SuperviseEngine
from tests.test_launch_engine import _make_repo
from tests.test_reconcile_engine import _write_launch, _write_observe_result

runner = CliRunner()


def _write_reconcile(project):
    observe_plan = ObserveEngine().build(project, target="codex")
    ObserveEngine().write_directory(observe_plan, project / "observe")
    supervise_plan = SuperviseEngine().build(project)
    SuperviseEngine().write_directory(supervise_plan, project / "supervise")
    reconcile_plan = ReconcileEngine().build(project)
    ReconcileEngine().write_directory(reconcile_plan, project / "reconcile")
    (project / "reconcile.json").write_text((project / "reconcile" / "reconcile.json").read_text(encoding="utf-8"), encoding="utf-8")


def test_resume_command_writes_packet_directory_and_json(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Retry this lane.")
    _write_reconcile(project)

    output_dir = tmp_path / "resume-report"
    result = runner.invoke(app, ["resume", str(project), "--output-dir", str(output_dir), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads("\n".join(result.output.splitlines()[1:]))
    assert payload["schema_version"] == "agentkit.resume.v1"
    assert payload["relaunch_now_lane_ids"] == ["lane-01"]
    assert (output_dir / "resume.md").exists()
    assert (output_dir / "resume.json").exists()
    assert (output_dir / "lanes" / "lane-01" / "resume.json").exists()


def test_resume_command_supports_explicit_reconcile_path(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Retry this lane.")
    _write_reconcile(project)

    result = runner.invoke(app, ["resume", str(project), "--reconcile-path", str(project / "reconcile" / "reconcile.json"), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["reconcile_path"].endswith("reconcile/reconcile.json")


def test_resume_help():
    result = runner.invoke(app, ["resume", "--help"])
    assert result.exit_code == 0
    assert "--reconcile-path" in result.output
    assert "--packet-dir" in result.output
