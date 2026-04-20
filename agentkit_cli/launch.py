from __future__ import annotations

import json
import shlex
import shutil
import subprocess
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any


_SUPPORTED_TARGETS = {"generic", "codex", "claude-code"}
_LOCAL_EXECUTION_TARGETS = {"codex", "claude-code"}
_TARGET_COMMANDS = {
    "generic": {
        "execution_mode": "manual",
        "required_tool": None,
        "runner": "manual handoff packet",
    },
    "codex": {
        "execution_mode": "local-subprocess",
        "required_tool": "codex",
        "runner": "codex exec --full-auto",
    },
    "claude-code": {
        "execution_mode": "local-subprocess",
        "required_tool": "claude",
        "runner": "claude --print --permission-mode bypassPermissions",
    },
}


class LaunchError(Exception):
    pass


@dataclass(frozen=True)
class LaunchDependency:
    lane_id: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"lane_id": self.lane_id, "reason": self.reason}


@dataclass(frozen=True)
class LaunchPacketPaths:
    handoff_dir: str
    handoff_markdown_path: str
    materialize_metadata_path: str
    stage_json_path: str
    stage_markdown_path: str

    def to_dict(self) -> dict[str, str]:
        return {
            "handoff_dir": self.handoff_dir,
            "handoff_markdown_path": self.handoff_markdown_path,
            "materialize_metadata_path": self.materialize_metadata_path,
            "stage_json_path": self.stage_json_path,
            "stage_markdown_path": self.stage_markdown_path,
        }


@dataclass(frozen=True)
class LaunchAction:
    lane_id: str
    title: str
    phase_id: str
    phase_index: int
    serialization_group: str
    branch_name: str
    worktree_name: str
    worktree_path: str
    owned_paths: list[str] = field(default_factory=list)
    dependencies: list[LaunchDependency] = field(default_factory=list)
    packet_paths: LaunchPacketPaths | None = None
    phase_notes: list[str] = field(default_factory=list)
    stage_notes: list[str] = field(default_factory=list)
    materialize_notes: list[str] = field(default_factory=list)
    launch_notes: list[str] = field(default_factory=list)
    source_state: str = ""
    source_state_reason: str = ""
    state: str = "ready"
    state_reason: str = ""
    execution_mode: str = "manual"
    required_tool: str | None = None
    runner: str = ""
    command: list[str] = field(default_factory=list)
    command_cwd: str = ""
    command_stdin_path: str | None = None
    display_command: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_name": self.branch_name,
            "command": list(self.command),
            "command_cwd": self.command_cwd,
            "command_stdin_path": self.command_stdin_path,
            "dependencies": [item.to_dict() for item in self.dependencies],
            "display_command": self.display_command,
            "execution_mode": self.execution_mode,
            "lane_id": self.lane_id,
            "launch_notes": list(self.launch_notes),
            "materialize_notes": list(self.materialize_notes),
            "owned_paths": list(self.owned_paths),
            "packet_paths": self.packet_paths.to_dict() if self.packet_paths else None,
            "phase_id": self.phase_id,
            "phase_index": self.phase_index,
            "phase_notes": list(self.phase_notes),
            "required_tool": self.required_tool,
            "runner": self.runner,
            "serialization_group": self.serialization_group,
            "source_state": self.source_state,
            "source_state_reason": self.source_state_reason,
            "stage_notes": list(self.stage_notes),
            "state": self.state,
            "state_reason": self.state_reason,
            "title": self.title,
            "worktree_name": self.worktree_name,
            "worktree_path": self.worktree_path,
        }


@dataclass(frozen=True)
class LaunchPlan:
    schema_version: str
    project_path: str
    target: str
    materialize_path: str
    launchable_lane_ids: list[str] = field(default_factory=list)
    launched_lane_ids: list[str] = field(default_factory=list)
    waiting_lane_ids: list[str] = field(default_factory=list)
    blocked_lane_ids: list[str] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)
    actions: list[LaunchAction] = field(default_factory=list)
    source_materialize: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "actions": [item.to_dict() for item in self.actions],
            "blocked_lane_ids": list(self.blocked_lane_ids),
            "instructions": list(self.instructions),
            "launched_lane_ids": list(self.launched_lane_ids),
            "launchable_lane_ids": list(self.launchable_lane_ids),
            "materialize_path": self.materialize_path,
            "project_path": self.project_path,
            "schema_version": self.schema_version,
            "source_materialize": self.source_materialize,
            "target": self.target,
            "waiting_lane_ids": list(self.waiting_lane_ids),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


class LaunchEngine:
    def __init__(self) -> None:
        self._materialize = MaterializeArtifactLoader()

    def build(self, project_dir: str | Path, *, target: str | None = None) -> LaunchPlan:
        root = Path(project_dir).expanduser().resolve()
        materialize_path, materialize = self._materialize.load(root)
        if materialize_path is None or materialize is None:
            raise FileNotFoundError(
                "No materialize.json artifact found. Save a materialize packet first, then run agentkit launch."
            )

        if str(materialize.get("schema_version") or "") != "agentkit.materialize.v1":
            raise LaunchError("Saved materialize artifact is not a supported agentkit.materialize.v1 packet.")

        materialize_target = self._normalize_target(str(materialize.get("target") or "generic"))
        if target is not None:
            requested_target = self._normalize_target(target)
            if requested_target != materialize_target:
                raise LaunchError(
                    f"Launch target {requested_target!r} does not match saved materialize target {materialize_target!r}."
                )

        project_path = Path(materialize.get("project_path") or root).expanduser().resolve()
        actions = self._build_actions(materialize=materialize, target=materialize_target)
        return self._plan_from_actions(
            materialize=materialize,
            materialize_path=materialize_path,
            project_path=project_path,
            target=materialize_target,
            actions=actions,
            launched_lane_ids=[],
        )

    def launch(self, project_dir: str | Path, *, target: str | None = None) -> LaunchPlan:
        plan = self.build(project_dir, target=target)
        if plan.target not in _LOCAL_EXECUTION_TARGETS:
            raise LaunchError(
                f"Target {plan.target!r} does not support explicit local execution. Use the launch packet manually."
            )

        blocked_actions = [item for item in plan.actions if item.state == "blocked"]
        if blocked_actions:
            summary = "; ".join(f"{item.lane_id}: {item.state_reason}" for item in blocked_actions)
            raise LaunchError(f"Cannot execute launch plan because blocked lanes remain: {summary}")

        ready_actions = [item for item in plan.actions if item.state == "ready"]
        if not ready_actions:
            raise LaunchError("No launchable lanes are available in the saved materialize packet.")

        required_tool = ready_actions[0].required_tool
        if required_tool is None:
            raise LaunchError(
                f"Target {plan.target!r} does not support explicit local execution. Use the launch packet manually."
            )
        if shutil.which(required_tool) is None:
            raise LaunchError(f"Required tool not found on PATH: {required_tool}")

        launched_lane_ids: list[str] = []
        executed_actions: list[LaunchAction] = []
        for action in plan.actions:
            if action.state != "ready":
                executed_actions.append(action)
                continue
            self._execute_action(action)
            launched_lane_ids.append(action.lane_id)
            executed_actions.append(
                replace(
                    action,
                    state="launched",
                    state_reason="Local launch command exited successfully.",
                    launch_notes=list(action.launch_notes)
                    + ["The saved local builder command was executed successfully from this worktree."],
                )
            )

        return self._plan_from_actions(
            materialize=plan.source_materialize,
            materialize_path=Path(plan.materialize_path),
            project_path=Path(plan.project_path),
            target=plan.target,
            actions=executed_actions,
            launched_lane_ids=launched_lane_ids,
        )

    def render_markdown(self, plan: LaunchPlan) -> str:
        lines = [
            f"# Launch plan: {Path(plan.project_path).name}",
            "",
            f"- Schema: `{plan.schema_version}`",
            f"- Project: `{plan.project_path}`",
            f"- Target: `{plan.target}`",
            f"- Materialize packet: `{plan.materialize_path}`",
            "",
            "## Summary",
            "",
            f"- Launchable lanes: {', '.join(plan.launchable_lane_ids) if plan.launchable_lane_ids else 'none'}",
            f"- Launched lanes: {', '.join(plan.launched_lane_ids) if plan.launched_lane_ids else 'none'}",
            f"- Waiting lanes: {', '.join(plan.waiting_lane_ids) if plan.waiting_lane_ids else 'none'}",
            f"- Blocked lanes: {', '.join(plan.blocked_lane_ids) if plan.blocked_lane_ids else 'none'}",
            "",
            "## Instructions",
            "",
        ]
        for item in plan.instructions:
            lines.append(f"- {item}")
        lines.extend(["", "## Actions", ""])
        for action in plan.actions:
            lines.append(f"### {action.lane_id}: {action.title}")
            lines.append("")
            lines.append(f"- State: `{action.state}`")
            if action.state_reason:
                lines.append(f"- Reason: {action.state_reason}")
            lines.append(f"- Source materialize state: `{action.source_state}`")
            if action.source_state_reason:
                lines.append(f"- Source reason: {action.source_state_reason}")
            lines.append(f"- Phase: `{action.phase_id}`")
            lines.append(f"- Serialization group: `{action.serialization_group}`")
            lines.append(f"- Branch: `{action.branch_name}`")
            lines.append(f"- Worktree path: `{action.worktree_path}`")
            lines.append(f"- Handoff path: `{action.packet_paths.handoff_markdown_path if action.packet_paths else '(missing)'}`")
            lines.append(f"- Runner: `{action.runner}`")
            lines.append(f"- Execution mode: `{action.execution_mode}`")
            if action.required_tool:
                lines.append(f"- Required tool: `{action.required_tool}`")
            lines.append(f"- Command: `{action.display_command}`")
            lines.append(f"- Owned paths: {', '.join(action.owned_paths) if action.owned_paths else '.'}")
            if action.dependencies:
                lines.append(
                    f"- Dependencies: {', '.join(f'{item.lane_id} ({item.reason})' for item in action.dependencies)}"
                )
            else:
                lines.append("- Dependencies: none")
            if action.packet_paths:
                lines.append(f"- Materialize metadata: `{action.packet_paths.materialize_metadata_path}`")
                lines.append(f"- Stage JSON: `{action.packet_paths.stage_json_path}`")
                lines.append(f"- Stage Markdown: `{action.packet_paths.stage_markdown_path}`")
            for note in action.phase_notes:
                lines.append(f"- Phase note: {note}")
            for note in action.stage_notes:
                lines.append(f"- Stage note: {note}")
            for note in action.materialize_notes:
                lines.append(f"- Materialize note: {note}")
            for note in action.launch_notes:
                lines.append(f"- Launch note: {note}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def write_directory(self, plan: LaunchPlan, output_dir: str | Path) -> Path:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "launch.md").write_text(self.render_markdown(plan), encoding="utf-8")
        (out / "launch.json").write_text(plan.to_json(), encoding="utf-8")
        lanes_dir = out / "lanes"
        for action in plan.actions:
            lane_dir = lanes_dir / action.lane_id
            lane_dir.mkdir(parents=True, exist_ok=True)
            lane_payload = json.dumps(action.to_dict(), indent=2, sort_keys=True) + "\n"
            (lane_dir / "launch.json").write_text(lane_payload, encoding="utf-8")
            (lane_dir / "launch.md").write_text(self._render_lane_markdown(action), encoding="utf-8")
            helper = lane_dir / self._helper_filename(plan.target)
            helper.write_text(self._render_helper_script(action, plan.target), encoding="utf-8")
            if plan.target != "generic":
                helper.chmod(0o755)
        return out

    def _render_lane_markdown(self, action: LaunchAction) -> str:
        lines = [
            f"# Launch lane: {action.lane_id}",
            "",
            f"- Title: {action.title}",
            f"- State: `{action.state}`",
            f"- Reason: {action.state_reason or 'n/a'}",
            f"- Worktree path: `{action.worktree_path}`",
            f"- Handoff path: `{action.packet_paths.handoff_markdown_path if action.packet_paths else '(missing)'}`",
            f"- Command: `{action.display_command}`",
            f"- Execution mode: `{action.execution_mode}`",
        ]
        if action.dependencies:
            lines.append(
                f"- Dependencies: {', '.join(f'{item.lane_id} ({item.reason})' for item in action.dependencies)}"
            )
        else:
            lines.append("- Dependencies: none")
        if action.launch_notes:
            lines.extend(["", "## Launch notes", ""])
            for note in action.launch_notes:
                lines.append(f"- {note}")
        return "\n".join(lines).rstrip() + "\n"

    def _helper_filename(self, target: str) -> str:
        if target == "generic":
            return "command.txt"
        return "launch.sh"

    def _render_helper_script(self, action: LaunchAction, target: str) -> str:
        if target == "generic":
            return action.display_command + "\n"
        return "#!/usr/bin/env bash\nset -euo pipefail\n" + action.display_command + "\n"

    def _build_actions(self, *, materialize: dict[str, Any], target: str) -> list[LaunchAction]:
        actions: list[LaunchAction] = []
        for lane in sorted(
            materialize.get("actions") or [],
            key=lambda item: (int(item.get("phase_index") or 0), str(item.get("lane_id") or "")),
        ):
            lane_id = str(lane.get("lane_id") or "lane-00")
            worktree_path = Path(str(lane.get("worktree_path") or "")).expanduser().resolve()
            packet_paths = self._resolve_packet_paths(lane, worktree_path)
            dependencies = [
                LaunchDependency(
                    lane_id=str(item.get("lane_id") or ""),
                    reason=str(item.get("reason") or ""),
                )
                for item in sorted(
                    lane.get("dependencies") or [],
                    key=lambda item: (str(item.get("lane_id") or ""), str(item.get("reason") or "")),
                )
            ]
            source_state = str(lane.get("state") or "")
            source_state_reason = str(lane.get("state_reason") or "")
            state, state_reason = self._resolve_launch_state(
                lane=lane,
                source_state=source_state,
                target=target,
                worktree_path=worktree_path,
                packet_paths=packet_paths,
                dependencies=dependencies,
            )
            command, command_cwd, command_stdin_path, display_command = self._launch_command(
                target=target,
                worktree_path=worktree_path,
                handoff_path=Path(packet_paths.handoff_markdown_path),
            )
            target_spec = _TARGET_COMMANDS[target]
            actions.append(
                LaunchAction(
                    lane_id=lane_id,
                    title=str(lane.get("title") or lane_id),
                    phase_id=str(lane.get("phase_id") or "phase-00"),
                    phase_index=int(lane.get("phase_index") or 0),
                    serialization_group=str(lane.get("serialization_group") or ""),
                    branch_name=str(lane.get("branch_name") or ""),
                    worktree_name=str(lane.get("worktree_name") or worktree_path.name),
                    worktree_path=str(worktree_path),
                    owned_paths=list(lane.get("owned_paths") or []),
                    dependencies=dependencies,
                    packet_paths=packet_paths,
                    phase_notes=list(lane.get("phase_notes") or []),
                    stage_notes=list(lane.get("stage_notes") or []),
                    materialize_notes=list(lane.get("materialize_notes") or []),
                    launch_notes=self._launch_notes(target=target, state=state, source_state=source_state),
                    source_state=source_state,
                    source_state_reason=source_state_reason,
                    state=state,
                    state_reason=state_reason,
                    execution_mode=str(target_spec["execution_mode"]),
                    required_tool=target_spec["required_tool"],
                    runner=str(target_spec["runner"]),
                    command=command,
                    command_cwd=str(command_cwd),
                    command_stdin_path=str(command_stdin_path) if command_stdin_path is not None else None,
                    display_command=display_command,
                )
            )
        return actions

    def _plan_from_actions(
        self,
        *,
        materialize: dict[str, Any],
        materialize_path: Path,
        project_path: Path,
        target: str,
        actions: list[LaunchAction],
        launched_lane_ids: list[str],
    ) -> LaunchPlan:
        launchable_lane_ids = [item.lane_id for item in actions if item.state == "ready"]
        waiting_lane_ids = [item.lane_id for item in actions if item.state == "waiting"]
        blocked_lane_ids = [item.lane_id for item in actions if item.state == "blocked"]
        instructions = [
            "Launch planning only reads saved materialize artifacts and never mutates remotes.",
            "Use --execute only when you want to run eligible local builder commands from the saved worktrees.",
        ]
        if target in _LOCAL_EXECUTION_TARGETS:
            instructions.append(
                f"Explicit local execution is available for `{target}` when the required CLI is installed."
            )
        else:
            instructions.append("Generic targets stay manual: open or paste the saved handoff packet into your chosen builder.")
        if waiting_lane_ids:
            instructions.append(
                f"Serialized waiting lanes stay paused until earlier ownership lanes finish: {', '.join(waiting_lane_ids)}."
            )
        if blocked_lane_ids:
            instructions.append(
                f"Blocked lanes need missing worktree or packet fixes before launch: {', '.join(blocked_lane_ids)}."
            )
        if launched_lane_ids:
            instructions.append(f"Executed local launch commands for: {', '.join(launched_lane_ids)}.")
        elif target in _LOCAL_EXECUTION_TARGETS:
            instructions.append("Default output is a dry launch plan only; no local builder subprocesses were started.")

        return LaunchPlan(
            schema_version="agentkit.launch.v1",
            project_path=str(project_path),
            target=target,
            materialize_path=str(materialize_path),
            launchable_lane_ids=launchable_lane_ids,
            launched_lane_ids=launched_lane_ids,
            waiting_lane_ids=waiting_lane_ids,
            blocked_lane_ids=blocked_lane_ids,
            instructions=instructions,
            actions=actions,
            source_materialize=materialize,
        )

    def _resolve_packet_paths(self, lane: dict[str, Any], worktree_path: Path) -> LaunchPacketPaths:
        packet_paths = lane.get("packet_paths") or {}
        handoff_dir = Path(str(packet_paths.get("handoff_dir") or (worktree_path / ".agentkit" / "materialize"))).expanduser().resolve()
        return LaunchPacketPaths(
            handoff_dir=str(handoff_dir),
            handoff_markdown_path=str(
                Path(str(packet_paths.get("handoff_markdown_path") or (handoff_dir / "handoff.md"))).expanduser().resolve()
            ),
            materialize_metadata_path=str(
                Path(str(packet_paths.get("metadata_json_path") or (handoff_dir / "materialize.json"))).expanduser().resolve()
            ),
            stage_json_path=str(
                Path(str(packet_paths.get("copied_stage_json_path") or (handoff_dir / "stage.json"))).expanduser().resolve()
            ),
            stage_markdown_path=str(
                Path(str(packet_paths.get("copied_stage_markdown_path") or (handoff_dir / "stage.md"))).expanduser().resolve()
            ),
        )

    def _resolve_launch_state(
        self,
        *,
        lane: dict[str, Any],
        source_state: str,
        target: str,
        worktree_path: Path,
        packet_paths: LaunchPacketPaths,
        dependencies: list[LaunchDependency],
    ) -> tuple[str, str]:
        if source_state == "waiting" or dependencies:
            return "waiting", str(lane.get("state_reason") or "Serialized lane must wait for earlier materialized work.")

        if source_state == "blocked":
            return "blocked", str(lane.get("state_reason") or "Materialize marked this lane as blocked.")

        if source_state != "materialized":
            return (
                "blocked",
                "Lane was not materialized into a local worktree. Run agentkit materialize without --dry-run first.",
            )

        if not worktree_path.exists():
            return "blocked", f"Expected materialized worktree is missing: {worktree_path}"

        materialize_metadata_path = Path(packet_paths.materialize_metadata_path)
        if not materialize_metadata_path.exists():
            return "blocked", f"Expected materialize lane metadata is missing: {materialize_metadata_path}"

        materialize_metadata = self._load_json(materialize_metadata_path)
        metadata_error = self._validate_lane_metadata(
            materialize_metadata=materialize_metadata,
            lane_id=str(lane.get("lane_id") or ""),
            target=target,
            worktree_path=worktree_path,
        )
        if metadata_error is not None:
            return "blocked", metadata_error

        handoff_path = Path(packet_paths.handoff_markdown_path)
        if not handoff_path.exists():
            return "blocked", f"Expected handoff markdown is missing: {handoff_path}"

        return "ready", "Eligible for deterministic launch planning from the saved materialize artifacts."

    def _validate_lane_metadata(
        self,
        *,
        materialize_metadata: dict[str, Any],
        lane_id: str,
        target: str,
        worktree_path: Path,
    ) -> str | None:
        if str(materialize_metadata.get("schema_version") or "") != "agentkit.materialize.lane.v1":
            return "Saved lane metadata is not a supported agentkit.materialize.lane.v1 packet."

        metadata_target = str(materialize_metadata.get("target") or "")
        if metadata_target and metadata_target != target:
            return f"Saved lane metadata target {metadata_target!r} does not match launch target {target!r}."

        lane = materialize_metadata.get("lane") or {}
        metadata_lane_id = str(lane.get("lane_id") or "")
        if metadata_lane_id != lane_id:
            return f"Saved lane metadata points at {metadata_lane_id or '(missing lane id)'}, expected {lane_id}."

        metadata_worktree = str(lane.get("worktree_path") or "")
        if metadata_worktree and Path(metadata_worktree).expanduser().resolve() != worktree_path:
            return f"Saved lane metadata worktree does not match the launch worktree path for {lane_id}."

        return None

    def _launch_command(
        self,
        *,
        target: str,
        worktree_path: Path,
        handoff_path: Path,
    ) -> tuple[list[str], Path, Path | None, str]:
        quoted_worktree = shlex.quote(str(worktree_path))
        quoted_handoff = shlex.quote(str(handoff_path))
        if target == "generic":
            command = ["cat", str(handoff_path)]
            return command, worktree_path, None, f"cd {quoted_worktree} && {shlex.join(command)}"
        if target == "codex":
            command = ["codex", "exec", "--full-auto", "-"]
            return command, worktree_path, handoff_path, f"cd {quoted_worktree} && codex exec --full-auto - < {quoted_handoff}"
        command = ["claude", "--print", "--permission-mode", "bypassPermissions"]
        return command, worktree_path, handoff_path, f"cd {quoted_worktree} && claude --print --permission-mode bypassPermissions < {quoted_handoff}"

    def _launch_notes(self, *, target: str, state: str, source_state: str) -> list[str]:
        notes: list[str]
        if target == "generic":
            notes = [
                "Generic launch stays manual: open or paste the handoff packet into the coding agent you are using.",
                "No local subprocess launcher is available for the generic target.",
            ]
        elif target == "codex":
            notes = [
                "Run Codex from the materialized worktree path so the lane stays isolated.",
                "The launch prompt is read from `.agentkit/materialize/handoff.md`.",
            ]
        else:
            notes = [
                "Run Claude Code from the materialized worktree path so the lane stays isolated.",
                "The launch prompt is read from `.agentkit/materialize/handoff.md`.",
            ]
        if state == "waiting":
            notes.append("This lane remains waiting until the earlier serialized lane finishes and is re-materialized.")
        elif state == "blocked":
            notes.append("Fix the blocked artifact or worktree state before attempting execution.")
        elif source_state == "materialized":
            notes.append("This lane is already materialized locally, so launch planning does not need to recreate worktrees.")
        return notes

    def _execute_action(self, action: LaunchAction) -> None:
        if action.required_tool is None:
            raise LaunchError(
                f"Target {action.runner!r} does not support explicit local execution. Use the launch packet manually."
            )

        if action.command_stdin_path is not None:
            with Path(action.command_stdin_path).open("r", encoding="utf-8") as handle:
                result = subprocess.run(
                    action.command,
                    capture_output=True,
                    text=True,
                    cwd=action.command_cwd,
                    stdin=handle,
                )
        else:
            result = subprocess.run(
                action.command,
                capture_output=True,
                text=True,
                cwd=action.command_cwd,
            )

        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "launch command failed"
            raise LaunchError(f"Failed to launch lane {action.lane_id}: {message}")

    def _load_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _normalize_target(self, target: str) -> str:
        value = target.strip().lower()
        if value not in _SUPPORTED_TARGETS:
            raise LaunchError("target must be one of: generic, codex, claude-code")
        return value


class MaterializeArtifactLoader:
    def load(self, project_dir: str | Path) -> tuple[Path | None, dict[str, Any] | None]:
        root = Path(project_dir).expanduser().resolve()
        for candidate in self._candidates(root):
            if candidate.exists() and candidate.is_file():
                return candidate.resolve(), json.loads(candidate.read_text(encoding="utf-8"))
        return None, None

    def _candidates(self, root: Path) -> list[Path]:
        direct = [
            root / "materialize.json",
            root / ".agentkit" / "materialize.json",
            root / "artifacts" / "materialize.json",
            root / "materialize" / "materialize.json",
            root / "stage" / "materialize.json",
        ]
        packet_dirs = (
            sorted(
                [
                    path
                    for path in root.iterdir()
                    if path.is_dir() and path.name.startswith(("materialize", "launch", "packet", "handoff", "stage"))
                ],
                key=lambda path: path.name,
            )
            if root.exists()
            else []
        )
        nested = [path / "materialize.json" for path in packet_dirs]
        return direct + nested
