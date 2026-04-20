from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.stage import StageEngine

runner = CliRunner()


def _make_repo(tmp_path: Path) -> Path:
    project = tmp_path / "demo-repo"
    (project / ".agentkit").mkdir(parents=True)
    (project / "src" / "api").mkdir(parents=True)
    (project / "src" / "worker").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / ".agentkit" / "source.md").write_text("# Demo Repo\n", encoding="utf-8")
    (project / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'api'\n", encoding="utf-8")
    (project / "src" / "worker" / "jobs.py").write_text("def run_job():\n    return 'worker'\n", encoding="utf-8")
    return project


def _write_dispatch(project: Path, *, target: str = "codex", overlap: bool = False) -> None:
    lanes = [
        {
            "lane_id": "lane-01",
            "title": "api",
            "phase_id": "phase-01",
            "phase_index": 1,
            "ownership_mode": "exclusive",
            "owned_paths": ["src/api", "tests/test_api.py"],
            "subsystem_hints": [],
            "dependencies": [],
            "packet": {"objective": "api", "runner": "codex exec --full-auto" if target == "codex" else "generic coding agent", "execution_notes": [], "stop_conditions": []},
        },
        {
            "lane_id": "lane-02",
            "title": "worker",
            "phase_id": "phase-02" if overlap else "phase-01",
            "phase_index": 2 if overlap else 1,
            "ownership_mode": "serialized-overlap" if overlap else "exclusive",
            "owned_paths": ["src/api/sub" if overlap else "src/worker", "tests/test_worker.py"],
            "subsystem_hints": [],
            "dependencies": [{"lane_id": "lane-01", "reason": "overlapping ownership: src/api"}] if overlap else [],
            "packet": {"objective": "worker", "runner": "codex exec --full-auto" if target == "codex" else "generic coding agent", "execution_notes": [], "stop_conditions": []},
        },
    ]
    phases = [
        {"phase_id": "phase-01", "index": 1, "execution_mode": "parallel" if not overlap else "serial", "lane_ids": ["lane-01"] if overlap else ["lane-01", "lane-02"], "rationale": "demo"},
    ]
    if overlap:
        phases.append({"phase_id": "phase-02", "index": 2, "execution_mode": "serial", "lane_ids": ["lane-02"], "rationale": "overlap"})
    payload = {
        "schema_version": "agentkit.dispatch.v1",
        "project_path": str(project),
        "target": target,
        "execution_recommendation": "proceed",
        "recommendation_reason": "Ready.",
        "worktree_guidance": ["Use separate worktrees or isolated branches per lane when phases contain more than one lane."],
        "phases": phases,
        "lanes": lanes,
        "ownership_conflicts": [{"left_lane_id": "lane-01", "right_lane_id": "lane-02", "overlap": "src/api"}] if overlap else [],
        "source_resolve": {},
        "source_taskpack": {},
        "source_bundle": {},
    }
    (project / "dispatch.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def test_stage_engine_builds_deterministic_lane_packets(tmp_path):
    project = _make_repo(tmp_path)
    _write_dispatch(project)

    manifest = StageEngine().build(project, target="codex", output_dir=tmp_path / "stage-out")

    assert manifest.schema_version == "agentkit.stage.v1"
    assert manifest.target == "codex"
    assert manifest.lanes[0].branch_name == "stage/phase-01/lane-01"
    assert manifest.lanes[0].worktree_name == "demo-repo-phase-01-lane-01"
    payload = json.loads(manifest.to_json())
    assert payload["lanes"][0]["packet_reference"]["json_path"] == "lanes/lane-01.json"


def test_stage_engine_preserves_serialization_constraints(tmp_path):
    project = _make_repo(tmp_path)
    _write_dispatch(project, overlap=True)

    manifest = StageEngine().build(project, target="codex", output_dir=tmp_path / "stage-out")

    assert len(manifest.phases) == 2
    assert manifest.lanes[1].serialization_group == "phase-02-serial"
    assert manifest.lanes[1].dependencies == [manifest.lanes[1].dependencies[0]]
    assert any("Wait for lane-01" in note for note in manifest.lanes[1].phase_notes)


def test_stage_command_writes_stage_directory(tmp_path):
    project = _make_repo(tmp_path)
    _write_dispatch(project, target="claude-code")
    output_dir = tmp_path / "stage"

    result = runner.invoke(app, ["stage", str(project), "--target", "claude-code", "--output-dir", str(output_dir)])

    assert result.exit_code == 0, result.output
    assert (output_dir / "stage.md").exists()
    assert (output_dir / "stage.json").exists()
    assert (output_dir / "lanes" / "lane-01" / "stage.json").exists()
    assert (output_dir / "lanes" / "lane-01" / "stage.md").exists()
    assert "Wrote stage directory" in result.output


def test_stage_command_supports_output_file(tmp_path):
    project = _make_repo(tmp_path)
    _write_dispatch(project)
    output = tmp_path / "stage.md"

    result = runner.invoke(app, ["stage", str(project), "--target", "codex", "--output", str(output)])

    assert result.exit_code == 0, result.output
    assert output.exists()
    assert "# Stage plan:" in output.read_text(encoding="utf-8")


def test_stage_command_requires_saved_dispatch_packet(tmp_path):
    project = _make_repo(tmp_path)

    result = runner.invoke(app, ["stage", str(project), "--json"])

    assert result.exit_code == 2
    assert "No dispatch.json artifact found" in result.output


def test_stage_command_validates_target_against_dispatch(tmp_path):
    project = _make_repo(tmp_path)
    _write_dispatch(project, target="generic")

    result = runner.invoke(app, ["stage", str(project), "--target", "codex", "--json"])

    assert result.exit_code == 2
    assert "does not match saved dispatch target" in result.output


def test_stage_target_notes_cover_all_supported_runners(tmp_path):
    project = _make_repo(tmp_path)
    _write_dispatch(project, target="generic")

    generic = StageEngine().build(project, target="generic", output_dir=tmp_path / "stage-generic")
    assert any("Create the suggested worktree or branch manually" in note for note in generic.lanes[0].stage_notes)

    payload = json.loads((project / "dispatch.json").read_text(encoding="utf-8"))
    payload["target"] = "claude-code"
    payload["lanes"][0]["packet"]["runner"] = "claude --print --permission-mode bypassPermissions"
    payload["lanes"][1]["packet"]["runner"] = "claude --print --permission-mode bypassPermissions"
    (project / "dispatch.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    claude = StageEngine().build(project, target="claude-code", output_dir=tmp_path / "stage-claude")
    assert any("run Claude Code" in note for note in claude.lanes[0].stage_notes)


def test_stage_help():
    result = runner.invoke(app, ["stage", "--help"])
    assert result.exit_code == 0
    assert "--output-dir" in result.output
    assert "--target" in result.output
