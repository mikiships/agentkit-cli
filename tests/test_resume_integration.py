from __future__ import annotations

import json
import subprocess

import pytest

from agentkit_cli.observe import ObserveEngine
from agentkit_cli.reconcile import ReconcileEngine
from agentkit_cli.resume import ResumeEngine, ResumeError
from agentkit_cli.supervise import SuperviseEngine
from tests.test_launch_engine import _make_repo
from tests.test_reconcile_engine import _git, _write_launch, _write_observe_result


def _save_chain(project):
    observe_plan = ObserveEngine().build(project, target="codex")
    ObserveEngine().write_directory(observe_plan, project / "observe")
    supervise_plan = SuperviseEngine().build(project)
    SuperviseEngine().write_directory(supervise_plan, project / "supervise")
    reconcile_plan = ReconcileEngine().build(project)
    ReconcileEngine().write_directory(reconcile_plan, project / "reconcile")
    (project / "reconcile.json").write_text((project / "reconcile" / "reconcile.json").read_text(encoding="utf-8"), encoding="utf-8")


def test_resume_engine_rejects_missing_launch_artifact_from_reconcile_chain(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Retry this lane.")
    _save_chain(project)

    payload = json.loads((project / "reconcile.json").read_text(encoding="utf-8"))
    payload["launch_path"] = str(project / "missing-launch.json")
    (project / "reconcile.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    with pytest.raises(ResumeError, match="missing launch packet"):
        ResumeEngine().build(project)


def test_resume_engine_is_planning_only_and_does_not_mutate_worktrees(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_chain(project)

    before = subprocess.run(["git", "-C", str(project), "status", "--short"], capture_output=True, text=True, check=True).stdout
    plan = ResumeEngine().build(project)
    after = subprocess.run(["git", "-C", str(project), "status", "--short"], capture_output=True, text=True, check=True).stdout

    assert plan.relaunch_now_lane_ids == ["lane-02"]
    assert before == after
