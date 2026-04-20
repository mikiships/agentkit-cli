from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_TARGET_STAGE_NOTES = {
    "generic": [
        "Create the suggested worktree or branch manually before handing this packet to a builder.",
        "Use the referenced lane packet as the execution handoff after the worktree exists.",
    ],
    "codex": [
        "Create the worktree first, then run Codex from the staged worktree path instead of the root repo.",
        "Attach or paste the lane packet after confirming the worktree path matches this plan.",
    ],
    "claude-code": [
        "Create the worktree first, then run Claude Code from the staged worktree path instead of the root repo.",
        "Paste the lane packet directly after confirming the branch and path match this stage plan.",
    ],
}


@dataclass(frozen=True)
class StageDependency:
    lane_id: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"lane_id": self.lane_id, "reason": self.reason}


@dataclass(frozen=True)
class StagePacketReference:
    json_path: str
    markdown_path: str

    def to_dict(self) -> dict[str, str]:
        return {"json_path": self.json_path, "markdown_path": self.markdown_path}


@dataclass(frozen=True)
class StageLane:
    lane_id: str
    title: str
    phase_id: str
    phase_index: int
    serialization_group: str
    branch_name: str
    worktree_name: str
    worktree_path: str
    owned_paths: list[str] = field(default_factory=list)
    dependencies: list[StageDependency] = field(default_factory=list)
    packet_reference: StagePacketReference | None = None
    phase_notes: list[str] = field(default_factory=list)
    stage_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_name": self.branch_name,
            "dependencies": [item.to_dict() for item in self.dependencies],
            "lane_id": self.lane_id,
            "owned_paths": list(self.owned_paths),
            "packet_reference": self.packet_reference.to_dict() if self.packet_reference else None,
            "phase_id": self.phase_id,
            "phase_index": self.phase_index,
            "phase_notes": list(self.phase_notes),
            "serialization_group": self.serialization_group,
            "stage_notes": list(self.stage_notes),
            "title": self.title,
            "worktree_name": self.worktree_name,
            "worktree_path": self.worktree_path,
        }


@dataclass(frozen=True)
class StagePhase:
    phase_id: str
    index: int
    execution_mode: str
    lane_ids: list[str] = field(default_factory=list)
    serialization_groups: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "execution_mode": self.execution_mode,
            "index": self.index,
            "lane_ids": list(self.lane_ids),
            "notes": list(self.notes),
            "phase_id": self.phase_id,
            "serialization_groups": list(self.serialization_groups),
        }


@dataclass(frozen=True)
class StageManifest:
    schema_version: str
    project_path: str
    target: str
    dispatch_path: str
    output_root: str
    phases: list[StagePhase] = field(default_factory=list)
    lanes: list[StageLane] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)
    source_dispatch: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "dispatch_path": self.dispatch_path,
            "instructions": list(self.instructions),
            "lanes": [item.to_dict() for item in self.lanes],
            "output_root": self.output_root,
            "phases": [item.to_dict() for item in self.phases],
            "project_path": self.project_path,
            "schema_version": self.schema_version,
            "source_dispatch": self.source_dispatch,
            "target": self.target,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


class StageEngine:
    def __init__(self) -> None:
        self._dispatch = DispatchArtifactLoader()

    def build(self, project_dir: str | Path, *, target: str = "generic", output_dir: str | Path | None = None) -> StageManifest:
        root = Path(project_dir).expanduser().resolve()
        normalized_target = self._normalize_target(target)
        dispatch_path, dispatch = self._dispatch.load(root)
        if dispatch is None or dispatch_path is None:
            raise FileNotFoundError(
                "No dispatch.json artifact found. Save a dispatch packet first, then run agentkit stage."
            )

        dispatch_target = str(dispatch.get("target") or normalized_target)
        if dispatch_target != normalized_target:
            raise ValueError(
                f"Stage target {normalized_target!r} does not match saved dispatch target {dispatch_target!r}."
            )

        out_root = Path(output_dir).expanduser().resolve() if output_dir is not None else (root / "stage")
        phases = self._build_phases(dispatch)
        lanes = self._build_lanes(dispatch, out_root, normalized_target)
        instructions = self._instructions(lanes, out_root)
        return StageManifest(
            schema_version="agentkit.stage.v1",
            project_path=str(root),
            target=normalized_target,
            dispatch_path=str(dispatch_path),
            output_root=str(out_root),
            phases=phases,
            lanes=lanes,
            instructions=instructions,
            source_dispatch=dispatch,
        )

    def render_markdown(self, manifest: StageManifest) -> str:
        lines = [
            f"# Stage plan: {Path(manifest.project_path).name}",
            "",
            f"- Schema: `{manifest.schema_version}`",
            f"- Project: `{manifest.project_path}`",
            f"- Target: `{manifest.target}`",
            f"- Dispatch: `{manifest.dispatch_path}`",
            f"- Output root: `{manifest.output_root}`",
            "",
            "## Runner instructions",
            "",
        ]
        for item in manifest.instructions:
            lines.append(f"- {item}")
        lines.extend(["", "## Phases", ""])
        for phase in manifest.phases:
            lines.append(f"### {phase.phase_id} ({phase.execution_mode})")
            lines.append("")
            lines.append(f"- Lanes: {', '.join(phase.lane_ids)}")
            lines.append(f"- Serialization groups: {', '.join(phase.serialization_groups) if phase.serialization_groups else '(none)'}")
            for note in phase.notes:
                lines.append(f"- Note: {note}")
            lines.append("")
        lines.extend(["## Lane staging packets", ""])
        for lane in manifest.lanes:
            lines.append(f"### {lane.lane_id}: {lane.title}")
            lines.append("")
            lines.append(f"- Phase: {lane.phase_id}")
            lines.append(f"- Serialization group: {lane.serialization_group}")
            lines.append(f"- Branch: `{lane.branch_name}`")
            lines.append(f"- Worktree name: `{lane.worktree_name}`")
            lines.append(f"- Worktree path: `{lane.worktree_path}`")
            lines.append(f"- Owned paths: {', '.join(lane.owned_paths) if lane.owned_paths else '.'}")
            if lane.dependencies:
                lines.append(f"- Dependencies: {', '.join(f'{item.lane_id} ({item.reason})' for item in lane.dependencies)}")
            else:
                lines.append("- Dependencies: none")
            if lane.packet_reference:
                lines.append(f"- Packet JSON: `{lane.packet_reference.json_path}`")
                lines.append(f"- Packet Markdown: `{lane.packet_reference.markdown_path}`")
            for note in lane.phase_notes:
                lines.append(f"- Phase note: {note}")
            for note in lane.stage_notes:
                lines.append(f"- Stage note: {note}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def write_directory(self, manifest: StageManifest, output_dir: str | Path) -> Path:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "stage.md").write_text(self.render_markdown(manifest), encoding="utf-8")
        (out / "stage.json").write_text(manifest.to_json(), encoding="utf-8")
        lanes_dir = out / "lanes"
        lanes_dir.mkdir(exist_ok=True)
        for lane in manifest.lanes:
            lane_dir = lanes_dir / lane.lane_id
            lane_dir.mkdir(exist_ok=True)
            (lane_dir / "stage.json").write_text(json.dumps(lane.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
            (lane_dir / "stage.md").write_text(self._render_lane_markdown(lane), encoding="utf-8")
        return out

    def _render_lane_markdown(self, lane: StageLane) -> str:
        lines = [
            f"# {lane.lane_id}: {lane.title}",
            "",
            f"- Phase: {lane.phase_id}",
            f"- Serialization group: {lane.serialization_group}",
            f"- Branch: `{lane.branch_name}`",
            f"- Worktree name: `{lane.worktree_name}`",
            f"- Worktree path: `{lane.worktree_path}`",
            f"- Owned paths: {', '.join(lane.owned_paths) if lane.owned_paths else '.'}",
        ]
        if lane.dependencies:
            lines.append(f"- Dependencies: {', '.join(f'{item.lane_id} ({item.reason})' for item in lane.dependencies)}")
        else:
            lines.append("- Dependencies: none")
        if lane.packet_reference:
            lines.append(f"- Packet JSON: `{lane.packet_reference.json_path}`")
            lines.append(f"- Packet Markdown: `{lane.packet_reference.markdown_path}`")
        lines.extend(["", "## Phase notes", ""])
        if lane.phase_notes:
            for note in lane.phase_notes:
                lines.append(f"- {note}")
        else:
            lines.append("- No phase-specific wait notes.")
        lines.extend(["", "## Stage notes", ""])
        for note in lane.stage_notes:
            lines.append(f"- {note}")
        return "\n".join(lines).rstrip() + "\n"

    def _build_phases(self, dispatch: dict[str, Any]) -> list[StagePhase]:
        phases = []
        for phase in sorted(dispatch.get("phases") or [], key=lambda item: (int(item.get("index") or 0), str(item.get("phase_id") or ""))):
            lane_ids = list(phase.get("lane_ids") or [])
            groups = [self._serialization_group(str(phase.get("phase_id") or "phase-00"), lane_id, str(phase.get("execution_mode") or "parallel")) for lane_id in lane_ids]
            notes = []
            if str(phase.get("execution_mode") or "") == "serial":
                notes.append("This phase stays serialized because dispatch found overlapping ownership.")
            else:
                notes.append("These lanes may be prepared in parallel, but execution still must honor owned paths.")
            phases.append(StagePhase(
                phase_id=str(phase.get("phase_id") or "phase-00"),
                index=int(phase.get("index") or 0),
                execution_mode=str(phase.get("execution_mode") or "parallel"),
                lane_ids=lane_ids,
                serialization_groups=groups,
                notes=notes,
            ))
        return phases

    def _build_lanes(self, dispatch: dict[str, Any], out_root: Path, target: str) -> list[StageLane]:
        lanes = []
        for lane in sorted(dispatch.get("lanes") or [], key=lambda item: str(item.get("lane_id") or "")):
            lane_id = str(lane.get("lane_id") or "lane-00")
            phase_id = str(lane.get("phase_id") or "phase-00")
            worktree_name = self._slug(f"{Path(dispatch.get('project_path') or out_root.parent).name}-{phase_id}-{lane_id}")
            branch_name = self._branch_name(phase_id, lane_id)
            worktree_path = out_root / "worktrees" / worktree_name
            packet_reference = StagePacketReference(
                json_path=f"lanes/{lane_id}.json",
                markdown_path=f"lanes/{lane_id}.md",
            )
            deps = [
                StageDependency(lane_id=str(item.get("lane_id") or ""), reason=str(item.get("reason") or ""))
                for item in sorted(lane.get("dependencies") or [], key=lambda item: (str(item.get("lane_id") or ""), str(item.get("reason") or "")))
            ]
            phase_notes = [f"Wait for {dep.lane_id} before creating or using this worktree because {dep.reason}." for dep in deps]
            stage_notes = list(_TARGET_STAGE_NOTES[target]) + [
                f"Only edit these owned paths from this worktree: {', '.join(lane.get('owned_paths') or ['.'])}.",
                f"Stage packet directory: lanes/{lane_id}/",
            ]
            lanes.append(StageLane(
                lane_id=lane_id,
                title=str(lane.get("title") or lane_id),
                phase_id=phase_id,
                phase_index=int(lane.get("phase_index") or 0),
                serialization_group=self._serialization_group(phase_id, lane_id, str(next((item.get('execution_mode') for item in dispatch.get('phases') or [] if item.get('phase_id') == phase_id), 'parallel'))),
                branch_name=branch_name,
                worktree_name=worktree_name,
                worktree_path=str(worktree_path),
                owned_paths=list(lane.get("owned_paths") or []),
                dependencies=deps,
                packet_reference=packet_reference,
                phase_notes=phase_notes,
                stage_notes=stage_notes,
            ))
        return lanes

    def _instructions(self, lanes: list[StageLane], out_root: Path) -> list[str]:
        instructions = [
            f"Write the portable stage directory to `{out_root}`.",
            "Create real git worktrees manually from the suggested branch and path values before handing packets to builders.",
            "Do not spawn agents or mutate external repos from this stage plan.",
        ]
        if len(lanes) <= 1:
            instructions.append("Single-lane stage plans still render one lane packet without inventing extra parallel lanes.")
        else:
            instructions.append("Prepare each lane in phase order and preserve serialized phases exactly as planned.")
        return instructions

    def _normalize_target(self, target: str) -> str:
        value = target.strip().lower()
        if value not in _TARGET_STAGE_NOTES:
            raise ValueError("target must be one of: generic, codex, claude-code")
        return value

    def _serialization_group(self, phase_id: str, lane_id: str, execution_mode: str) -> str:
        if execution_mode == "serial":
            return f"{phase_id}-serial"
        return f"{phase_id}-{lane_id}"

    def _branch_name(self, phase_id: str, lane_id: str) -> str:
        return f"stage/{self._slug(phase_id)}/{self._slug(lane_id)}"

    def _slug(self, value: str) -> str:
        cleaned = [ch.lower() if ch.isalnum() else "-" for ch in value]
        result = "".join(cleaned)
        while "--" in result:
            result = result.replace("--", "-")
        return result.strip("-")


class DispatchArtifactLoader:
    def load(self, project_dir: str | Path) -> tuple[Path | None, dict[str, Any] | None]:
        root = Path(project_dir).expanduser().resolve()
        for candidate in self._candidates(root):
            if candidate.exists() and candidate.is_file():
                return candidate, json.loads(candidate.read_text(encoding="utf-8"))
        return None, None

    def _candidates(self, root: Path) -> list[Path]:
        direct = [
            root / "dispatch.json",
            root / ".agentkit" / "dispatch.json",
            root / "artifacts" / "dispatch.json",
        ]
        packet_dirs = sorted(
            [path for path in root.iterdir() if path.is_dir() and path.name.startswith(("dispatch", "stage", "packet", "handoff"))],
            key=lambda path: path.name,
        ) if root.exists() else []
        nested = [path / "dispatch.json" for path in packet_dirs]
        return direct + nested
