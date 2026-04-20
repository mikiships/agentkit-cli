from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.dispatch import DispatchEngine
from agentkit_cli.main import app

runner = CliRunner()


def _make_repo(tmp_path: Path) -> Path:
    project = tmp_path / "demo-repo"
    (project / ".agentkit").mkdir(parents=True)
    (project / "src" / "api").mkdir(parents=True)
    (project / "src" / "worker").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / ".agentkit" / "source.md").write_text(
        "# Demo Repo\n\n"
        "## Objective\nShip deterministic dispatch planning.\n\n"
        "## Scope & Boundaries\nWork only inside this repo.\n\n"
        "## Rules\n- Keep output deterministic.\n\n"
        "## Validation\nRun pytest.\n\n"
        "## Deliverables\nLeave dispatch artifacts in markdown and JSON.\n",
        encoding="utf-8",
    )
    (project / "pyproject.toml").write_text(
        "[project]\nname='demo-repo'\nversion='0.1.0'\n\n[project.scripts]\ndemo='src.main:main'\n",
        encoding="utf-8",
    )
    (project / "src" / "main.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (project / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'api'\n", encoding="utf-8")
    (project / "src" / "worker" / "jobs.py").write_text("def run_job():\n    return 'worker'\n", encoding="utf-8")
    (project / "tests" / "test_api.py").write_text("def test_api():\n    assert True\n", encoding="utf-8")
    (project / "tests" / "test_worker.py").write_text("def test_worker():\n    assert True\n", encoding="utf-8")
    (project / "all-day-build-contract-demo.md").write_text("# Demo contract\n\n- Keep output deterministic.\n", encoding="utf-8")
    return project


def _write_resolve(project: Path, *, recommendation: str = "proceed") -> None:
    (project / "resolve.json").write_text(
        json.dumps(
            {
                "schema_version": "agentkit.resolve.v1",
                "project_path": str(project),
                "answers_path": str(project / "answers.json"),
                "execution_recommendation": recommendation,
                "recommendation_reason": "Saved resolve packet is ready for planning.",
                "resolved_questions": [],
                "remaining_blockers": [] if recommendation != "pause" else [{"code": "missing_answer", "title": "Missing answer", "status": "unanswered", "answer": "", "source_section": "blocking_questions", "kind": "question", "rationale": "Needs an answer."}],
                "remaining_follow_ups": [],
                "confirmed_assumptions": [],
                "superseded_assumptions": [],
                "unresolved_assumptions": [],
                "answers_summary": {"remaining_blockers": 0 if recommendation != "pause" else 1},
                "source_clarify": {},
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_dispatch_engine_builds_parallel_lanes_from_saved_resolve(tmp_path):
    project = _make_repo(tmp_path)
    _write_resolve(project)

    plan = DispatchEngine().build(project, target="codex")

    assert plan.schema_version == "agentkit.dispatch.v1"
    assert plan.execution_recommendation == "proceed"
    assert len(plan.phases) == 1
    assert plan.phases[0].execution_mode == "parallel"
    assert len(plan.lanes) >= 2
    assert all(lane.packet and lane.packet.runner == "codex exec --full-auto" for lane in plan.lanes)
    payload = json.loads(plan.to_json())
    assert payload["target"] == "codex"


def test_dispatch_engine_serializes_overlapping_owned_paths(tmp_path):
    project = _make_repo(tmp_path)
    _write_resolve(project)
    payload = json.loads((project / "resolve.json").read_text(encoding="utf-8"))
    payload["source_clarify"] = {
        "source_bundle": {
            "architecture_map": {
                "subsystems": [
                    {"name": "src", "path": "src", "why": "All app code"},
                    {"name": "api", "path": "src/api", "why": "API handlers"},
                ],
                "tests": [],
                "hints": [],
            }
        }
    }
    (project / "resolve.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    plan = DispatchEngine().build(project)

    assert len(plan.phases) >= 2
    assert any(lane.ownership_mode == "serialized-overlap" for lane in plan.lanes)
    assert plan.ownership_conflicts


def test_dispatch_engine_pauses_when_resolve_has_blockers(tmp_path):
    project = _make_repo(tmp_path)
    _write_resolve(project, recommendation="pause")

    plan = DispatchEngine().build(project)

    assert plan.execution_recommendation == "pause"
    assert len(plan.lanes) == 1


def test_dispatch_command_writes_packet_directory(tmp_path):
    project = _make_repo(tmp_path)
    _write_resolve(project)
    output_dir = tmp_path / "dispatch-packet"

    result = runner.invoke(app, ["dispatch", str(project), "--output-dir", str(output_dir)])

    assert result.exit_code == 0, result.output
    assert (output_dir / "dispatch.md").exists()
    assert (output_dir / "dispatch.json").exists()
    assert any(path.name.endswith('.md') for path in (output_dir / 'lanes').iterdir())
    assert "Wrote dispatch directory" in result.output


def test_dispatch_packets_include_target_notes_and_worktree_guidance(tmp_path):
    project = _make_repo(tmp_path)
    _write_resolve(project)

    plan = DispatchEngine().build(project, target="claude-code")

    assert len(plan.lanes) >= 2
    assert any("Use separate worktrees or isolated branches per lane" in item for item in plan.worktree_guidance)
    for lane in plan.lanes:
        assert lane.packet is not None
        assert lane.packet.objective
        assert lane.packet.runner == "claude --print --permission-mode bypassPermissions"
        assert any("Owned paths:" in note for note in lane.packet.execution_notes)
        assert any("Stop if the work requires files outside the owned paths." == stop for stop in lane.packet.stop_conditions)


def test_dispatch_markdown_single_lane_does_not_claim_parallelism(tmp_path):
    project = _make_repo(tmp_path)
    _write_resolve(project, recommendation="pause")

    plan = DispatchEngine().build(project, target="generic")
    markdown = DispatchEngine().render_markdown(plan)

    assert len(plan.lanes) == 1
    assert "Single-lane plan, so no fake parallelism is claimed." in markdown
    assert "generic coding agent" in markdown


def test_dispatch_command_requires_saved_resolve_packet(tmp_path):
    project = _make_repo(tmp_path)

    result = runner.invoke(app, ["dispatch", str(project), "--json"])

    assert result.exit_code == 2
    assert "No resolve.json artifact found" in result.output


def test_dispatch_help():
    result = runner.invoke(app, ["dispatch", "--help"])
    assert result.exit_code == 0
    assert "--output-dir" in result.output
    assert "--target" in result.output
