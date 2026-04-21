from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Any

from agentkit_cli.schemas import RelaunchDependency, RelaunchLane, RelaunchPlan

_SUPPORTED_TARGETS = {"generic", "codex", "claude-code"}
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


class RelaunchError(Exception):
    pass


class RelaunchEngine:
    def build(
        self,
        project_dir: str | Path,
        *,
        resume_path: str | Path | None = None,
        packet_dir: str | Path | None = None,
    ) -> RelaunchPlan:
        root = Path(project_dir).expanduser().resolve()
        resolved_resume_path, resume = self._load_resume(root, resume_path=resume_path)
        resolved_reconcile_path, reconcile = self._load_required_json(
            Path(str(resume.get("reconcile_path") or "")),
            label="reconcile packet from resume plan",
        )
        resolved_launch_path, launch = self._load_required_json(
            Path(str(resume.get("launch_path") or "")),
            label="launch packet from resume plan",
        )
        observe_path = self._optional_file(resume.get("observe_path"))
        supervise_path = self._optional_file(resume.get("supervise_path"))
        if supervise_path is None:
            raise RelaunchError("Saved resume artifact is incomplete: supervise_path is required for deterministic relaunch planning.")

        self._validate_resume_shape(resume)
        self._validate_reconcile_shape(reconcile, resume_path=resolved_resume_path, launch_path=resolved_launch_path)

        launch_actions = {str(item.get("lane_id") or ""): item for item in launch.get("actions") or []}
        reconcile_lanes = {str(item.get("lane_id") or ""): item for item in reconcile.get("lanes") or []}
        if not launch_actions:
            raise RelaunchError("Saved relaunch evidence is incomplete: launch.actions is required.")

        resolved_packet_dir = Path(packet_dir).expanduser().resolve() if packet_dir else None
        relaunch_now: list[str] = []
        waiting: list[str] = []
        review: list[str] = []
        completed: list[str] = []
        lanes: list[RelaunchLane] = []

        for item in sorted(
            resume.get("lanes") or [],
            key=lambda lane: (int(lane.get("phase_index") or 0), str(lane.get("lane_id") or "")),
        ):
            lane_id = str(item.get("lane_id") or "")
            launch_action = launch_actions.get(lane_id)
            reconcile_lane = reconcile_lanes.get(lane_id)
            if launch_action is None or reconcile_lane is None:
                raise RelaunchError(f"Saved relaunch evidence is contradictory: lane {lane_id!r} is missing from upstream launch or reconcile artifacts.")

            dependencies = [
                RelaunchDependency(
                    lane_id=str(dep.get("lane_id") or ""),
                    reason=str(dep.get("reason") or ""),
                    satisfied=bool(dep.get("satisfied")),
                )
                for dep in item.get("dependencies") or []
            ]
            resume_bucket = str(item.get("resume_bucket") or "")
            reconcile_bucket = str(reconcile_lane.get("bucket") or "")
            self._validate_lane_alignment(
                lane_id=lane_id,
                resume_bucket=resume_bucket,
                reconcile_bucket=reconcile_bucket,
                dependencies=dependencies,
            )

            packet_path = str(resolved_packet_dir / "lanes" / lane_id / "relaunch.json") if resolved_packet_dir else None
            handoff_markdown_path = str(resolved_packet_dir / "lanes" / lane_id / "handoff.md") if resolved_packet_dir and resume_bucket == "relaunch-now" else None
            helper_path = None
            source_handoff_path = self._source_launch_handoff_path(launch_action)
            review_notes = self._review_notes(
                resume_bucket=resume_bucket,
                worktree_path=str(launch_action.get("worktree_path") or item.get("worktree_path") or ""),
                source_handoff_path=source_handoff_path,
                review_lane_ids=[str(value) for value in resume.get("review_lane_ids") or []],
            )
            display_command = ""
            execution_mode = "manual"
            required_tool = None
            runner = "manual handoff packet"
            if handoff_markdown_path is not None:
                helper_path = str(resolved_packet_dir / "lanes" / lane_id / self._helper_filename(str(resume.get("target") or "generic")))
                display_command = self._display_command(
                    target=str(resume.get("target") or "generic"),
                    worktree_path=str(launch_action.get("worktree_path") or item.get("worktree_path") or ""),
                    handoff_markdown_path=handoff_markdown_path,
                )
                target_spec = _TARGET_COMMANDS[str(resume.get("target") or "generic")]
                execution_mode = str(target_spec["execution_mode"])
                required_tool = target_spec["required_tool"]
                runner = str(target_spec["runner"])

            lane = RelaunchLane(
                lane_id=lane_id,
                title=str(item.get("title") or lane_id),
                phase_id=str(item.get("phase_id") or "phase-00"),
                phase_index=int(item.get("phase_index") or 0),
                serialization_group=str(item.get("serialization_group") or ""),
                branch_name=str(launch_action.get("branch_name") or item.get("branch_name") or ""),
                worktree_path=str(launch_action.get("worktree_path") or item.get("worktree_path") or ""),
                relaunch_bucket=resume_bucket,
                reason=str(item.get("reason") or ""),
                next_action=str(item.get("next_action") or ""),
                source_resume_bucket=resume_bucket,
                source_reconcile_bucket=reconcile_bucket,
                dependencies=dependencies,
                eligibility_reason=self._eligibility_reason(
                    lane_id=lane_id,
                    resume_bucket=resume_bucket,
                    reconcile_bucket=reconcile_bucket,
                    reason=str(item.get("reason") or ""),
                ),
                upstream_evidence_paths=self._upstream_evidence_paths(
                    resolved_resume_path=resolved_resume_path,
                    resolved_reconcile_path=resolved_reconcile_path,
                    resolved_launch_path=resolved_launch_path,
                    observe_path=observe_path,
                    supervise_path=supervise_path,
                    source_handoff_path=source_handoff_path,
                ),
                review_notes=review_notes,
                source_resume_path=str(resolved_resume_path),
                source_launch_handoff_path=source_handoff_path,
                packet_path=packet_path,
                handoff_markdown_path=handoff_markdown_path,
                helper_path=helper_path,
                execution_mode=execution_mode,
                required_tool=required_tool,
                runner=runner,
                display_command=display_command,
            )
            lanes.append(lane)
            if resume_bucket == "relaunch-now":
                relaunch_now.append(lane_id)
            elif resume_bucket == "waiting":
                waiting.append(lane_id)
            elif resume_bucket == "review-only":
                review.append(lane_id)
            elif resume_bucket == "completed":
                completed.append(lane_id)
            else:
                raise RelaunchError(f"Saved resume artifact is contradictory: unsupported resume bucket {resume_bucket!r} for lane {lane_id!r}.")

        next_actions = [
            "Relaunch planning is local-only and never mutates git state, worktrees, tags, or remotes.",
        ]
        if review:
            next_actions.append(f"Human review is still required before execution for: {', '.join(review)}.")
        if relaunch_now:
            next_actions.append(f"Fresh relaunch packets are ready for: {', '.join(relaunch_now)}.")
        if waiting:
            next_actions.append(f"Keep these lanes waiting until prerequisites clear: {', '.join(waiting)}.")
        if completed:
            next_actions.append(f"Preserve completed lanes as closed unless a human explicitly reopens them: {', '.join(completed)}.")
        if not relaunch_now and not waiting and not review and not completed:
            next_actions.append("No lanes remain in the saved resume artifact.")

        return RelaunchPlan(
            schema_version="agentkit.relaunch.v1",
            project_path=str(Path(resume.get("project_path") or root).expanduser().resolve()),
            target=self._normalize_target(str(resume.get("target") or "generic")),
            resume_path=str(resolved_resume_path),
            reconcile_path=str(resolved_reconcile_path),
            launch_path=str(resolved_launch_path),
            observe_path=str(observe_path) if observe_path else None,
            supervise_path=str(supervise_path) if supervise_path else None,
            relaunch_now_lane_ids=relaunch_now,
            waiting_lane_ids=waiting,
            review_lane_ids=review,
            completed_lane_ids=completed,
            packet_dir=str(resolved_packet_dir) if resolved_packet_dir else None,
            next_actions=next_actions,
            lanes=lanes,
        )

    def render_markdown(self, plan: RelaunchPlan) -> str:
        lines = [
            f"# Relaunch plan: {Path(plan.project_path).name}",
            "",
            f"- Schema: `{plan.schema_version}`",
            f"- Project: `{plan.project_path}`",
            f"- Target: `{plan.target}`",
            f"- Resume packet: `{plan.resume_path}`",
            f"- Reconcile packet: `{plan.reconcile_path}`",
            f"- Launch packet: `{plan.launch_path}`",
            f"- Observe packet: `{plan.observe_path or 'not found'}`",
            f"- Supervise packet: `{plan.supervise_path or 'not found'}`",
            "",
            "## Summary",
            "",
            f"- Relaunch now: {', '.join(plan.relaunch_now_lane_ids) if plan.relaunch_now_lane_ids else 'none'}",
            f"- Waiting: {', '.join(plan.waiting_lane_ids) if plan.waiting_lane_ids else 'none'}",
            f"- Review only: {', '.join(plan.review_lane_ids) if plan.review_lane_ids else 'none'}",
            f"- Completed: {', '.join(plan.completed_lane_ids) if plan.completed_lane_ids else 'none'}",
            "",
            "## Next actions",
            "",
        ]
        for item in plan.next_actions:
            lines.append(f"- {item}")
        lines.extend(["", "## Lanes", ""])
        for lane in plan.lanes:
            lines.extend(
                [
                    f"### {lane.lane_id}: {lane.title}",
                    "",
                    f"- Relaunch bucket: `{lane.relaunch_bucket}`",
                    f"- Resume reason: {lane.reason}",
                    f"- Eligibility: {lane.eligibility_reason}",
                    f"- Next action: {lane.next_action}",
                    f"- Reconcile bucket: `{lane.source_reconcile_bucket}`",
                    f"- Branch: `{lane.branch_name}`",
                    f"- Worktree path: `{lane.worktree_path or 'unknown'}`",
                    f"- Source launch handoff: `{lane.source_launch_handoff_path or 'not found'}`",
                    f"- Fresh handoff: `{lane.handoff_markdown_path or 'not written'}`",
                    f"- Runner: `{lane.runner}`",
                    f"- Command: `{lane.display_command or 'manual review required'}`",
                ]
            )
            if lane.dependencies:
                lines.append(
                    "- Dependencies: " + ", ".join(f"{dep.lane_id} ({'satisfied' if dep.satisfied else 'pending'})" for dep in lane.dependencies)
                )
            else:
                lines.append("- Dependencies: none")
            for note in lane.review_notes:
                lines.append(f"- Review note: {note}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def write_directory(self, plan: RelaunchPlan, output_dir: str | Path) -> Path:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "relaunch.md").write_text(self.render_markdown(plan), encoding="utf-8")
        (out / "relaunch.json").write_text(plan.to_json(), encoding="utf-8")
        lanes_dir = out / "lanes"
        for lane in plan.lanes:
            lane_dir = lanes_dir / lane.lane_id
            lane_dir.mkdir(parents=True, exist_ok=True)
            (lane_dir / "relaunch.json").write_text(json.dumps(lane.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (lane_dir / "relaunch.md").write_text(self._render_lane_markdown(lane), encoding="utf-8")
            if lane.handoff_markdown_path is not None:
                (lane_dir / "handoff.md").write_text(self._render_handoff_markdown(lane), encoding="utf-8")
            if lane.helper_path is not None:
                helper = lane_dir / Path(lane.helper_path).name
                helper.write_text(self._render_helper(lane), encoding="utf-8")
                if helper.name != "command.txt":
                    helper.chmod(0o755)
        return out

    def _render_lane_markdown(self, lane: RelaunchLane) -> str:
        lines = [
            f"# Relaunch lane: {lane.lane_id}",
            "",
            f"- Title: {lane.title}",
            f"- Bucket: `{lane.relaunch_bucket}`",
            f"- Resume reason: {lane.reason}",
            f"- Eligibility: {lane.eligibility_reason}",
            f"- Reconcile bucket: `{lane.source_reconcile_bucket}`",
            f"- Worktree path: `{lane.worktree_path or 'unknown'}`",
            f"- Fresh handoff: `{lane.handoff_markdown_path or 'not written'}`",
            f"- Command: `{lane.display_command or 'manual review required'}`",
        ]
        if lane.dependencies:
            dependency_summary = ", ".join(
                f"{item.lane_id} ({'satisfied' if item.satisfied else 'pending'})" for item in lane.dependencies
            )
            lines.append(f"- Dependencies: {dependency_summary}")
        else:
            lines.append("- Dependencies: none")
        if lane.review_notes:
            lines.extend(["", "## Review notes", ""])
            for note in lane.review_notes:
                lines.append(f"- {note}")
        return "\n".join(lines).rstrip() + "\n"

    def _render_handoff_markdown(self, lane: RelaunchLane) -> str:
        lines = [
            f"# Relaunch handoff: {lane.lane_id}",
            "",
            "Use this packet to restart the saved lane intentionally from the preserved resume decision.",
            "",
            "## Resume decision",
            "",
            f"- Lane: `{lane.lane_id}`",
            f"- Title: {lane.title}",
            f"- Relaunch bucket: `{lane.relaunch_bucket}`",
            f"- Resume reason: {lane.reason}",
            f"- Eligibility reason: {lane.eligibility_reason}",
            f"- Reconcile bucket: `{lane.source_reconcile_bucket}`",
            f"- Branch: `{lane.branch_name}`",
            f"- Worktree path: `{lane.worktree_path or 'unknown'}`",
            f"- Source launch handoff: `{lane.source_launch_handoff_path or 'not found'}`",
            "",
            "## Upstream evidence",
            "",
        ]
        for path in lane.upstream_evidence_paths:
            lines.append(f"- `{path}`")
        if lane.dependencies:
            lines.extend(["", "## Dependencies", ""])
            for dep in lane.dependencies:
                lines.append(f"- {dep.lane_id}: {dep.reason} ({'satisfied' if dep.satisfied else 'pending'})")
        if lane.review_notes:
            lines.extend(["", "## Human review before execution", ""])
            for note in lane.review_notes:
                lines.append(f"- {note}")
        lines.extend(
            [
                "",
                "## Next runner instructions",
                "",
                f"- Run from the lane worktree if it still exists: `{lane.worktree_path or 'unknown'}`.",
                f"- Feed this packet to the target runner: `{lane.runner}`.",
                f"- Preferred command: `{lane.display_command or 'manual review required before execution'}`.",
                "- Review any unresolved review-only lanes before executing this restart.",
                "- This relaunch packet is planning-only and does not itself recreate worktrees or execute the builder.",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    def _render_helper(self, lane: RelaunchLane) -> str:
        if not lane.display_command:
            return "manual review required before execution\n"
        if lane.helper_path and Path(lane.helper_path).name == "command.txt":
            return lane.display_command + "\n"
        return "#!/usr/bin/env bash\nset -euo pipefail\n" + lane.display_command + "\n"

    def _helper_filename(self, target: str) -> str:
        return "command.txt" if target == "generic" else "launch.sh"

    def _display_command(self, *, target: str, worktree_path: str, handoff_markdown_path: str) -> str:
        quoted_handoff = shlex.quote(handoff_markdown_path)
        resolved_worktree = str(Path(worktree_path).expanduser().resolve()) if worktree_path else ""
        quoted_worktree = shlex.quote(resolved_worktree) if resolved_worktree else ""
        if not resolved_worktree or not Path(resolved_worktree).exists():
            if target == "generic":
                return f"cat {quoted_handoff}"
            if target == "codex":
                return f"# recreate the lane worktree, then run: codex exec --full-auto - < {quoted_handoff}"
            return f"# recreate the lane worktree, then run: claude --print --permission-mode bypassPermissions < {quoted_handoff}"
        if target == "generic":
            return f"cd {quoted_worktree} && cat {quoted_handoff}"
        if target == "codex":
            return f"cd {quoted_worktree} && codex exec --full-auto - < {quoted_handoff}"
        return f"cd {quoted_worktree} && claude --print --permission-mode bypassPermissions < {quoted_handoff}"

    def _eligibility_reason(self, *, lane_id: str, resume_bucket: str, reconcile_bucket: str, reason: str) -> str:
        if resume_bucket == "relaunch-now":
            if reconcile_bucket == "relaunch-ready":
                return reason or f"Lane {lane_id} failed cleanly and is ready for a fresh pass."
            return reason or f"Lane {lane_id} is newly unblocked and safe to relaunch now."
        if resume_bucket == "waiting":
            return reason or f"Lane {lane_id} must keep waiting for prerequisites or serialized ownership."
        if resume_bucket == "review-only":
            return reason or f"Lane {lane_id} needs manual review before any restart."
        return reason or f"Lane {lane_id} is already complete."

    def _review_notes(self, *, resume_bucket: str, worktree_path: str, source_handoff_path: str | None, review_lane_ids: list[str]) -> list[str]:
        notes: list[str] = []
        if review_lane_ids:
            notes.append(f"Saved resume evidence still contains review-only lanes: {', '.join(review_lane_ids)}.")
        if worktree_path and not Path(worktree_path).expanduser().resolve().exists():
            notes.append(f"Saved worktree path is stale or missing, so recreate or repair it before executing the relaunch: {Path(worktree_path).expanduser().resolve()}")
        if source_handoff_path and not Path(source_handoff_path).expanduser().resolve().exists():
            notes.append(f"The original launch handoff packet is missing, so trust the fresh relaunch handoff instead: {Path(source_handoff_path).expanduser().resolve()}")
        if resume_bucket != "relaunch-now":
            notes.append("This lane is preserved for visibility only and should not be relaunched from this packet.")
        return notes

    def _upstream_evidence_paths(
        self,
        *,
        resolved_resume_path: Path,
        resolved_reconcile_path: Path,
        resolved_launch_path: Path,
        observe_path: Path | None,
        supervise_path: Path | None,
        source_handoff_path: str | None,
    ) -> list[str]:
        paths = [str(resolved_resume_path), str(resolved_reconcile_path), str(resolved_launch_path)]
        if observe_path is not None:
            paths.append(str(observe_path))
        if supervise_path is not None:
            paths.append(str(supervise_path))
        if source_handoff_path:
            paths.append(source_handoff_path)
        return paths

    def _source_launch_handoff_path(self, launch_action: dict[str, Any]) -> str | None:
        packet_paths = launch_action.get("packet_paths") or {}
        value = str(packet_paths.get("handoff_markdown_path") or "").strip()
        return str(Path(value).expanduser().resolve()) if value else None

    def _normalize_target(self, target: str) -> str:
        value = target.strip().lower()
        if value not in _SUPPORTED_TARGETS:
            raise RelaunchError("target must be one of: generic, codex, claude-code")
        return value

    def _load_resume(self, root: Path, *, resume_path: str | Path | None) -> tuple[Path, dict[str, Any]]:
        candidates: list[Path]
        if resume_path is None:
            candidates = [
                root / "resume.json",
                root / "resume" / "resume.json",
                root / "artifacts" / "resume.json",
                root / ".agentkit" / "resume.json",
            ]
        else:
            requested = Path(resume_path).expanduser().resolve()
            candidates = [requested / "resume.json"] if requested.is_dir() else [requested]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate.resolve(), self._read_json(candidate)
        raise FileNotFoundError("No resume.json artifact found. Save a resume packet first, then run agentkit relaunch.")

    def _load_required_json(self, path: Path, *, label: str) -> tuple[Path, dict[str, Any]]:
        value = str(path).strip()
        if not value:
            raise RelaunchError(f"Saved resume artifact is incomplete: missing {label}.")
        if not path.exists() or not path.is_file():
            raise RelaunchError(f"Saved resume artifact points at a missing {label}: {path}")
        return path.resolve(), self._read_json(path)

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RelaunchError(f"Saved relaunch evidence is malformed JSON: {path}") from exc
        if not isinstance(data, dict):
            raise RelaunchError(f"Saved relaunch evidence must be a JSON object: {path}")
        return data

    def _optional_file(self, path: Any) -> Path | None:
        value = str(path or "").strip()
        if not value:
            return None
        candidate = Path(value).expanduser().resolve()
        if not candidate.exists() or not candidate.is_file():
            raise RelaunchError(f"Saved resume artifact points at a missing upstream artifact: {candidate}")
        return candidate

    def _validate_resume_shape(self, resume: dict[str, Any]) -> None:
        if str(resume.get("schema_version") or "") != "agentkit.resume.v1":
            raise RelaunchError("Saved resume artifact is not a supported agentkit.resume.v1 packet.")
        lane_ids: set[str] = set()
        summary = {
            "relaunch-now": {str(item) for item in resume.get("relaunch_now_lane_ids") or []},
            "waiting": {str(item) for item in resume.get("waiting_lane_ids") or []},
            "review-only": {str(item) for item in resume.get("review_lane_ids") or []},
            "completed": {str(item) for item in resume.get("completed_lane_ids") or []},
        }
        for lane in resume.get("lanes") or []:
            lane_id = str(lane.get("lane_id") or "")
            bucket = str(lane.get("resume_bucket") or "")
            if not lane_id or lane_id in lane_ids:
                raise RelaunchError(f"Saved resume artifact is contradictory: duplicate or empty lane id {lane_id!r}.")
            lane_ids.add(lane_id)
            if bucket not in summary or lane_id not in summary[bucket]:
                raise RelaunchError(f"Saved resume artifact is contradictory: lane {lane_id!r} bucket {bucket!r} disagrees with summary ids.")

    def _validate_reconcile_shape(self, reconcile: dict[str, Any], *, resume_path: Path, launch_path: Path) -> None:
        if str(reconcile.get("schema_version") or "") != "agentkit.reconcile.v1":
            raise RelaunchError("Saved reconcile artifact is not a supported agentkit.reconcile.v1 packet.")
        if Path(str(reconcile.get("launch_path") or "")).expanduser().resolve() != launch_path.resolve():
            raise RelaunchError("Saved relaunch evidence is contradictory: reconcile.launch_path does not match resume.launch_path.")
        if not str(resume_path):
            raise RelaunchError("Saved relaunch evidence is contradictory: missing resume path.")

    def _validate_lane_alignment(
        self,
        *,
        lane_id: str,
        resume_bucket: str,
        reconcile_bucket: str,
        dependencies: list[RelaunchDependency],
    ) -> None:
        allowed = {
            "relaunch-now": {"ready", "relaunch-ready"},
            "waiting": {"waiting"},
            "review-only": {"blocked", "drifted", "needs-human-review", "still-running"},
            "completed": {"complete"},
        }
        if resume_bucket not in allowed:
            raise RelaunchError(f"Saved resume artifact is contradictory: unsupported resume bucket {resume_bucket!r} for lane {lane_id!r}.")
        if reconcile_bucket not in allowed[resume_bucket]:
            raise RelaunchError(
                f"Saved relaunch evidence is contradictory: lane {lane_id!r} resume bucket {resume_bucket!r} disagrees with reconcile bucket {reconcile_bucket!r}."
            )
        if resume_bucket == "relaunch-now" and any(not dep.satisfied for dep in dependencies):
            raise RelaunchError(
                f"Saved relaunch evidence is contradictory: lane {lane_id!r} cannot relaunch now while dependencies remain unsatisfied."
            )
