from __future__ import annotations

import json
import shlex
import shutil
import subprocess
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any


_SUPPORTED_TARGETS = {"generic", "codex", "claude-code"}


class MaterializeError(Exception):
    pass


@dataclass(frozen=True)
class MaterializeDependency:
    lane_id: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"lane_id": self.lane_id, "reason": self.reason}


@dataclass(frozen=True)
class MaterializePacketPaths:
    source_json_path: str | None
    source_markdown_path: str | None
    handoff_dir: str
    copied_stage_json_path: str
    copied_stage_markdown_path: str
    metadata_json_path: str
    handoff_markdown_path: str

    def to_dict(self) -> dict[str, str | None]:
        return {
            "copied_stage_json_path": self.copied_stage_json_path,
            "copied_stage_markdown_path": self.copied_stage_markdown_path,
            "handoff_dir": self.handoff_dir,
            "handoff_markdown_path": self.handoff_markdown_path,
            "metadata_json_path": self.metadata_json_path,
            "source_json_path": self.source_json_path,
            "source_markdown_path": self.source_markdown_path,
        }


@dataclass(frozen=True)
class MaterializeAction:
    lane_id: str
    title: str
    phase_id: str
    phase_index: int
    serialization_group: str
    branch_name: str
    worktree_name: str
    worktree_path: str
    owned_paths: list[str] = field(default_factory=list)
    dependencies: list[MaterializeDependency] = field(default_factory=list)
    packet_paths: MaterializePacketPaths | None = None
    phase_notes: list[str] = field(default_factory=list)
    stage_notes: list[str] = field(default_factory=list)
    state: str = "ready"
    state_reason: str = ""
    command: list[str] = field(default_factory=list)
    materialize_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_name": self.branch_name,
            "command": list(self.command),
            "dependencies": [item.to_dict() for item in self.dependencies],
            "lane_id": self.lane_id,
            "materialize_notes": list(self.materialize_notes),
            "owned_paths": list(self.owned_paths),
            "packet_paths": self.packet_paths.to_dict() if self.packet_paths else None,
            "phase_id": self.phase_id,
            "phase_index": self.phase_index,
            "phase_notes": list(self.phase_notes),
            "serialization_group": self.serialization_group,
            "stage_notes": list(self.stage_notes),
            "state": self.state,
            "state_reason": self.state_reason,
            "title": self.title,
            "worktree_name": self.worktree_name,
            "worktree_path": self.worktree_path,
        }


@dataclass(frozen=True)
class MaterializePlan:
    schema_version: str
    project_path: str
    target: str
    stage_path: str
    stage_output_root: str
    worktree_root: str
    dry_run: bool
    base_commit: str
    eligible_lane_ids: list[str] = field(default_factory=list)
    materialized_lane_ids: list[str] = field(default_factory=list)
    waiting_lane_ids: list[str] = field(default_factory=list)
    blocked_lane_ids: list[str] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)
    actions: list[MaterializeAction] = field(default_factory=list)
    source_stage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "actions": [item.to_dict() for item in self.actions],
            "base_commit": self.base_commit,
            "blocked_lane_ids": list(self.blocked_lane_ids),
            "dry_run": self.dry_run,
            "eligible_lane_ids": list(self.eligible_lane_ids),
            "instructions": list(self.instructions),
            "materialized_lane_ids": list(self.materialized_lane_ids),
            "project_path": self.project_path,
            "schema_version": self.schema_version,
            "source_stage": self.source_stage,
            "stage_output_root": self.stage_output_root,
            "stage_path": self.stage_path,
            "target": self.target,
            "waiting_lane_ids": list(self.waiting_lane_ids),
            "worktree_root": self.worktree_root,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


class MaterializeEngine:
    def __init__(self) -> None:
        self._stage = StageArtifactLoader()

    def build(
        self,
        project_dir: str | Path,
        *,
        target: str | None = None,
        worktree_root: str | Path | None = None,
        dry_run: bool = True,
    ) -> MaterializePlan:
        root = Path(project_dir).expanduser().resolve()
        stage_path, stage = self._stage.load(root)
        if stage_path is None or stage is None:
            raise FileNotFoundError(
                "No stage.json artifact found. Save a stage packet first, then run agentkit materialize."
            )

        if str(stage.get("schema_version") or "") != "agentkit.stage.v1":
            raise MaterializeError("Saved stage artifact is not a supported agentkit.stage.v1 packet.")

        project_path = Path(stage.get("project_path") or root).expanduser().resolve()
        stage_target = self._normalize_target(str(stage.get("target") or "generic"))
        if target is not None:
            requested_target = self._normalize_target(target)
            if requested_target != stage_target:
                raise MaterializeError(
                    f"Materialize target {requested_target!r} does not match saved stage target {stage_target!r}."
                )
        repo_root = self._git_root(project_path)
        base_commit = self._git_stdout(repo_root, ["rev-parse", "--verify", "HEAD"])
        stage_output_root = Path(stage.get("output_root") or stage_path.parent).expanduser().resolve()
        resolved_worktree_root = self._resolve_worktree_root(stage, stage_output_root, worktree_root)
        actions = self._build_actions(
            stage=stage,
            stage_path=stage_path,
            repo_root=repo_root,
            worktree_root=resolved_worktree_root,
            base_commit=base_commit,
        )
        return self._plan_from_actions(
            stage=stage,
            stage_path=stage_path,
            project_path=repo_root,
            worktree_root=resolved_worktree_root,
            stage_output_root=stage_output_root,
            base_commit=base_commit,
            target=stage_target,
            dry_run=dry_run,
            actions=actions,
            materialized_lane_ids=[],
        )

    def materialize(
        self,
        project_dir: str | Path,
        *,
        target: str | None = None,
        worktree_root: str | Path | None = None,
        dry_run: bool = False,
    ) -> MaterializePlan:
        plan = self.build(project_dir, target=target, worktree_root=worktree_root, dry_run=dry_run)
        if dry_run:
            return plan

        blocked_ready = [item for item in plan.actions if item.state == "blocked" and not item.dependencies]
        if blocked_ready:
            summary = "; ".join(f"{item.lane_id}: {item.state_reason}" for item in blocked_ready)
            raise MaterializeError(f"Cannot materialize because ready lanes are blocked: {summary}")

        materialized_lane_ids: list[str] = []
        executed_actions: list[MaterializeAction] = []
        for action in plan.actions:
            if action.state != "ready":
                executed_actions.append(action)
                continue
            self._execute_action(Path(plan.project_path), plan.base_commit, action, plan.target, Path(plan.stage_path))
            materialized_lane_ids.append(action.lane_id)
            executed_actions.append(
                replace(
                    action,
                    state="materialized",
                    state_reason="Created the local worktree and seeded .agentkit/materialize for this lane.",
                    materialize_notes=list(action.materialize_notes)
                    + ["Local handoff files were copied into the created worktree."],
                )
            )

        return self._plan_from_actions(
            stage=plan.source_stage,
            stage_path=Path(plan.stage_path),
            project_path=Path(plan.project_path),
            worktree_root=Path(plan.worktree_root),
            stage_output_root=Path(plan.stage_output_root),
            base_commit=plan.base_commit,
            target=plan.target,
            dry_run=False,
            actions=executed_actions,
            materialized_lane_ids=materialized_lane_ids,
        )

    def render_markdown(self, plan: MaterializePlan) -> str:
        lines = [
            f"# Materialize plan: {Path(plan.project_path).name}",
            "",
            f"- Schema: `{plan.schema_version}`",
            f"- Project: `{plan.project_path}`",
            f"- Target: `{plan.target}`",
            f"- Stage: `{plan.stage_path}`",
            f"- Stage output root: `{plan.stage_output_root}`",
            f"- Worktree root: `{plan.worktree_root}`",
            f"- Base commit: `{plan.base_commit}`",
            f"- Dry run: {'yes' if plan.dry_run else 'no'}",
            "",
            "## Summary",
            "",
            f"- Eligible lanes: {', '.join(plan.eligible_lane_ids) if plan.eligible_lane_ids else 'none'}",
            f"- Materialized lanes: {', '.join(plan.materialized_lane_ids) if plan.materialized_lane_ids else 'none'}",
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
            lines.append(f"- Phase: {action.phase_id}")
            lines.append(f"- Serialization group: {action.serialization_group}")
            lines.append(f"- Branch: `{action.branch_name}`")
            lines.append(f"- Worktree path: `{action.worktree_path}`")
            lines.append(f"- Handoff dir: `{action.packet_paths.handoff_dir if action.packet_paths else '(missing)'}`")
            lines.append(f"- Owned paths: {', '.join(action.owned_paths) if action.owned_paths else '.'}")
            if action.dependencies:
                lines.append(
                    f"- Dependencies: {', '.join(f'{item.lane_id} ({item.reason})' for item in action.dependencies)}"
                )
            else:
                lines.append("- Dependencies: none")
            if action.packet_paths:
                lines.append(f"- Stage packet JSON: `{action.packet_paths.source_json_path or '(missing)'}`")
                lines.append(f"- Stage packet Markdown: `{action.packet_paths.source_markdown_path or '(missing)'}`")
                lines.append(f"- Seeded JSON path: `{action.packet_paths.copied_stage_json_path}`")
                lines.append(f"- Seeded Markdown path: `{action.packet_paths.copied_stage_markdown_path}`")
                lines.append(f"- Lane metadata: `{action.packet_paths.metadata_json_path}`")
                lines.append(f"- Handoff markdown: `{action.packet_paths.handoff_markdown_path}`")
            if action.command:
                lines.append(f"- Command: `{shlex.join(action.command)}`")
            for note in action.phase_notes:
                lines.append(f"- Phase note: {note}")
            for note in action.stage_notes:
                lines.append(f"- Stage note: {note}")
            for note in action.materialize_notes:
                lines.append(f"- Materialize note: {note}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def write_directory(self, plan: MaterializePlan, output_dir: str | Path) -> Path:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "materialize.md").write_text(self.render_markdown(plan), encoding="utf-8")
        (out / "materialize.json").write_text(plan.to_json(), encoding="utf-8")
        return out

    def _build_actions(
        self,
        *,
        stage: dict[str, Any],
        stage_path: Path,
        repo_root: Path,
        worktree_root: Path,
        base_commit: str,
    ) -> list[MaterializeAction]:
        actions: list[MaterializeAction] = []
        for lane in sorted(
            stage.get("lanes") or [],
            key=lambda item: (int(item.get("phase_index") or 0), str(item.get("lane_id") or "")),
        ):
            lane_id = str(lane.get("lane_id") or "lane-00")
            dependencies = [
                MaterializeDependency(
                    lane_id=str(item.get("lane_id") or ""),
                    reason=str(item.get("reason") or ""),
                )
                for item in sorted(
                    lane.get("dependencies") or [],
                    key=lambda item: (str(item.get("lane_id") or ""), str(item.get("reason") or "")),
                )
            ]
            worktree_name = str(lane.get("worktree_name") or Path(str(lane.get("worktree_path") or lane_id)).name)
            worktree_path = worktree_root / worktree_name
            packet_paths = self._resolve_packet_paths(stage_path, lane_id, worktree_path)
            command = [
                "git",
                "-C",
                str(repo_root),
                "worktree",
                "add",
                "-b",
                str(lane.get("branch_name") or ""),
                str(worktree_path),
                base_commit,
            ]
            phase_notes = list(lane.get("phase_notes") or [])
            stage_notes = list(lane.get("stage_notes") or [])
            materialize_notes = [
                "Local-only materialization: no agents are spawned and no remote repositories are mutated.",
                f"Branches start from commit {base_commit}.",
                "The created worktree is seeded at `.agentkit/materialize/` for the next builder handoff.",
            ]
            if dependencies:
                materialize_notes.append("This lane is preserved as waiting because earlier serialized ownership must finish first.")

            state = "ready"
            state_reason = "Eligible for local worktree creation."
            if dependencies:
                state = "waiting"
                state_reason = "Serialized lane must wait for dependency lanes before materialization."
            elif packet_paths.source_json_path is None or packet_paths.source_markdown_path is None:
                state = "blocked"
                state_reason = "Required lane packet files are missing from the saved stage directory."
            else:
                collisions = self._collision_reasons(
                    repo_root=repo_root,
                    worktree_path=worktree_path,
                    branch_name=str(lane.get("branch_name") or ""),
                )
                if collisions:
                    state = "blocked"
                    state_reason = collisions[0]
                    materialize_notes.extend(collisions)

            actions.append(
                MaterializeAction(
                    lane_id=lane_id,
                    title=str(lane.get("title") or lane_id),
                    phase_id=str(lane.get("phase_id") or "phase-00"),
                    phase_index=int(lane.get("phase_index") or 0),
                    serialization_group=str(lane.get("serialization_group") or ""),
                    branch_name=str(lane.get("branch_name") or ""),
                    worktree_name=worktree_name,
                    worktree_path=str(worktree_path),
                    owned_paths=list(lane.get("owned_paths") or []),
                    dependencies=dependencies,
                    packet_paths=packet_paths,
                    phase_notes=phase_notes,
                    stage_notes=stage_notes,
                    state=state,
                    state_reason=state_reason,
                    command=command if not dependencies else [],
                    materialize_notes=materialize_notes,
                )
            )
        return actions

    def _plan_from_actions(
        self,
        *,
        stage: dict[str, Any],
        stage_path: Path,
        project_path: Path,
        worktree_root: Path,
        stage_output_root: Path,
        base_commit: str,
        target: str,
        dry_run: bool,
        actions: list[MaterializeAction],
        materialized_lane_ids: list[str],
    ) -> MaterializePlan:
        eligible_lane_ids = [item.lane_id for item in actions if item.state == "ready"]
        waiting_lane_ids = [item.lane_id for item in actions if item.state == "waiting"]
        blocked_lane_ids = [item.lane_id for item in actions if item.state == "blocked"]
        instructions = [
            "Dry-run mode only inspects stage packets, git refs, and filesystem collisions without creating worktrees."
            if dry_run
            else "Local worktrees were created only for eligible lanes; waiting lanes were left untouched.",
            "Local-only materialization preserves the saved stage target and never spawns agents or mutates remotes.",
            "Re-run materialize after finishing earlier serialized lanes if you need to create the next waiting worktree.",
        ]
        if waiting_lane_ids:
            instructions.append(
                f"Serialized waiting lanes remain paused until dependencies finish: {', '.join(waiting_lane_ids)}."
            )
        if blocked_lane_ids:
            instructions.append(
                f"Blocked lanes need packet or collision fixes before they can materialize: {', '.join(blocked_lane_ids)}."
            )
        if materialized_lane_ids:
            instructions.append(f"Created worktrees for: {', '.join(materialized_lane_ids)}.")
        elif not dry_run:
            instructions.append("No eligible lanes were materialized in this run.")

        return MaterializePlan(
            schema_version="agentkit.materialize.v1",
            project_path=str(project_path),
            target=target,
            stage_path=str(stage_path),
            stage_output_root=str(stage_output_root),
            worktree_root=str(worktree_root),
            dry_run=dry_run,
            base_commit=base_commit,
            eligible_lane_ids=eligible_lane_ids,
            materialized_lane_ids=materialized_lane_ids,
            waiting_lane_ids=waiting_lane_ids,
            blocked_lane_ids=blocked_lane_ids,
            instructions=instructions,
            actions=actions,
            source_stage=stage,
        )

    def _resolve_worktree_root(
        self,
        stage: dict[str, Any],
        stage_output_root: Path,
        worktree_root: str | Path | None,
    ) -> Path:
        if worktree_root is not None:
            return Path(worktree_root).expanduser().resolve()

        lane_parents = {
            Path(str(item.get("worktree_path") or "")).expanduser().resolve().parent
            for item in stage.get("lanes") or []
            if str(item.get("worktree_path") or "").strip()
        }
        if len(lane_parents) == 1:
            return next(iter(lane_parents))
        return (stage_output_root / "worktrees").resolve()

    def _resolve_packet_paths(self, stage_path: Path, lane_id: str, worktree_path: Path) -> MaterializePacketPaths:
        stage_dir = stage_path.parent
        handoff_dir = worktree_path / ".agentkit" / "materialize"
        source_json = self._first_existing(
            [
                stage_dir / "lanes" / lane_id / "stage.json",
                stage_dir / "lanes" / f"{lane_id}.json",
            ]
        )
        source_markdown = self._first_existing(
            [
                stage_dir / "lanes" / lane_id / "stage.md",
                stage_dir / "lanes" / f"{lane_id}.md",
            ]
        )
        return MaterializePacketPaths(
            source_json_path=str(source_json) if source_json else None,
            source_markdown_path=str(source_markdown) if source_markdown else None,
            handoff_dir=str(handoff_dir),
            copied_stage_json_path=str(handoff_dir / "stage.json"),
            copied_stage_markdown_path=str(handoff_dir / "stage.md"),
            metadata_json_path=str(handoff_dir / "materialize.json"),
            handoff_markdown_path=str(handoff_dir / "handoff.md"),
        )

    def _collision_reasons(self, *, repo_root: Path, worktree_path: Path, branch_name: str) -> list[str]:
        reasons: list[str] = []
        if worktree_path.exists():
            reasons.append(f"Worktree path already exists: {worktree_path}")
        if self._branch_exists(repo_root, branch_name):
            reasons.append(f"Branch already exists: {branch_name}")
        if self._worktree_registered(repo_root, worktree_path):
            reasons.append(f"Worktree path is already registered with git: {worktree_path}")
        return reasons

    def _execute_action(
        self,
        repo_root: Path,
        base_commit: str,
        action: MaterializeAction,
        target: str,
        stage_path: Path,
    ) -> None:
        if action.packet_paths is None:
            raise MaterializeError(f"Lane {action.lane_id} is missing packet path metadata.")
        if action.packet_paths.source_json_path is None or action.packet_paths.source_markdown_path is None:
            raise MaterializeError(f"Lane {action.lane_id} is missing stage packet files.")

        worktree_path = Path(action.worktree_path)
        worktree_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            action.command,
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "git worktree add failed"
            raise MaterializeError(f"Failed to create worktree for {action.lane_id}: {message}")

        handoff_dir = Path(action.packet_paths.handoff_dir)
        handoff_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(action.packet_paths.source_json_path, action.packet_paths.copied_stage_json_path)
        shutil.copy2(action.packet_paths.source_markdown_path, action.packet_paths.copied_stage_markdown_path)
        metadata = {
            "schema_version": "agentkit.materialize.lane.v1",
            "base_commit": base_commit,
            "project_path": str(repo_root),
            "stage_path": str(stage_path),
            "target": target,
            "lane": replace(
                action,
                state="materialized",
                state_reason="Created the local worktree and seeded .agentkit/materialize for this lane.",
            ).to_dict(),
        }
        Path(action.packet_paths.metadata_json_path).write_text(
            json.dumps(metadata, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        Path(action.packet_paths.handoff_markdown_path).write_text(
            self._render_handoff_markdown(action, target),
            encoding="utf-8",
        )

    def _render_handoff_markdown(self, action: MaterializeAction, target: str) -> str:
        lines = [
            f"# Materialized lane: {action.lane_id}",
            "",
            f"- Target: `{target}`",
            f"- Phase: `{action.phase_id}`",
            f"- Serialization group: `{action.serialization_group}`",
            f"- Branch: `{action.branch_name}`",
            f"- Worktree path: `{action.worktree_path}`",
            f"- Owned paths: {', '.join(action.owned_paths) if action.owned_paths else '.'}",
        ]
        if action.dependencies:
            lines.append(
                f"- Dependencies: {', '.join(f'{item.lane_id} ({item.reason})' for item in action.dependencies)}"
            )
        else:
            lines.append("- Dependencies: none")
        lines.extend(["", "## Stage notes", ""])
        if action.stage_notes:
            for note in action.stage_notes:
                lines.append(f"- {note}")
        else:
            lines.append("- No stage notes were saved for this lane.")
        lines.extend(["", "## Phase notes", ""])
        if action.phase_notes:
            for note in action.phase_notes:
                lines.append(f"- {note}")
        else:
            lines.append("- No phase-specific wait notes were saved for this lane.")
        lines.extend(["", "## Materialize notes", ""])
        for note in action.materialize_notes:
            lines.append(f"- {note}")
        lines.extend(
            [
                "",
                "## Seeded files",
                "",
                "- `stage.json` copied from the saved stage lane packet",
                "- `stage.md` copied from the saved stage lane packet",
                "- `materialize.json` with machine-readable lane metadata",
                "- `handoff.md` with the target-aware handoff summary you are reading now",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    def _branch_exists(self, repo_root: Path, branch_name: str) -> bool:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def _worktree_registered(self, repo_root: Path, worktree_path: Path) -> bool:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False
        target = str(worktree_path.resolve())
        return any(line.strip() == f"worktree {target}" for line in result.stdout.splitlines())

    def _first_existing(self, candidates: list[Path]) -> Path | None:
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate.resolve()
        return None

    def _normalize_target(self, target: str) -> str:
        value = target.strip().lower()
        if value not in _SUPPORTED_TARGETS:
            raise MaterializeError("target must be one of: generic, codex, claude-code")
        return value

    def _git_root(self, project_dir: Path) -> Path:
        return Path(self._git_stdout(project_dir, ["rev-parse", "--show-toplevel"])).resolve()

    def _git_stdout(self, cwd: Path, args: list[str]) -> str:
        result = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "git command failed"
            raise MaterializeError(message)
        return result.stdout.strip()


class StageArtifactLoader:
    def load(self, project_dir: str | Path) -> tuple[Path | None, dict[str, Any] | None]:
        root = Path(project_dir).expanduser().resolve()
        for candidate in self._candidates(root):
            if candidate.exists() and candidate.is_file():
                return candidate.resolve(), json.loads(candidate.read_text(encoding="utf-8"))
        return None, None

    def _candidates(self, root: Path) -> list[Path]:
        direct = [
            root / "stage.json",
            root / ".agentkit" / "stage.json",
            root / "artifacts" / "stage.json",
            root / "stage" / "stage.json",
        ]
        packet_dirs = (
            sorted(
                [path for path in root.iterdir() if path.is_dir() and path.name.startswith(("stage", "packet", "handoff"))],
                key=lambda path: path.name,
            )
            if root.exists()
            else []
        )
        nested = [path / "stage.json" for path in packet_dirs]
        return direct + nested
