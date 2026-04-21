from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agentkit_cli.schemas import ResumeDependency, ResumeLane, ResumePlan


class ResumeError(Exception):
    pass


class ResumeEngine:
    def build(self, project_dir: str | Path, *, reconcile_path: str | Path | None = None, packet_dir: str | Path | None = None) -> ResumePlan:
        root = Path(project_dir).expanduser().resolve()
        resolved_reconcile_path, reconcile = self._load_reconcile(root, reconcile_path=reconcile_path)
        launch_path = self._require_file(Path(str(reconcile.get("launch_path") or "")), "launch packet from reconcile plan")
        observe_path = self._optional_file(reconcile.get("observe_path"))
        supervise_path = self._optional_file(reconcile.get("supervise_path"))
        if supervise_path is None:
            raise ResumeError("Saved reconcile artifact is incomplete: supervise_path is required for deterministic resume planning.")
        if not isinstance(reconcile.get("lanes"), list) or not reconcile["lanes"]:
            raise ResumeError("Saved reconcile artifact is incomplete: no lane records were found.")

        self._validate_reconcile_shape(reconcile)
        source_launch = reconcile.get("source_launch") or {}
        launch_actions = {str(item.get("lane_id") or ""): item for item in source_launch.get("actions") or []}
        if not launch_actions:
            raise ResumeError("Saved reconcile artifact is incomplete: source_launch.actions is required.")

        completed_source: set[str] = set()
        occupied_groups: set[str] = set()
        lanes: list[ResumeLane] = []
        relaunch_now: list[str] = []
        waiting: list[str] = []
        review: list[str] = []
        done: list[str] = []
        resolved_packet_dir = Path(packet_dir).expanduser().resolve() if packet_dir else None

        for item in sorted(reconcile["lanes"], key=lambda lane: (int(lane.get("phase_index") or 0), str(lane.get("lane_id") or ""))):
            lane_id = str(item.get("lane_id") or "")
            if lane_id not in launch_actions:
                raise ResumeError(f"Saved reconcile artifact is contradictory: lane {lane_id!r} is missing from source_launch.actions.")
            deps = [
                ResumeDependency(
                    lane_id=str(dep.get("lane_id") or ""),
                    reason=str(dep.get("reason") or ""),
                    satisfied=bool(dep.get("satisfied")),
                )
                for dep in item.get("dependencies") or []
            ]
            if any(dep.satisfied != (dep.lane_id in completed_source) for dep in deps):
                raise ResumeError(f"Saved reconcile artifact is contradictory: dependency satisfaction for lane {lane_id!r} does not match completed lanes in order.")
            bucket = str(item.get("bucket") or "")
            serialization_group = str(item.get("serialization_group") or "")
            resume_bucket, reason, next_action = self._resume_bucket(item, deps, occupied_groups)
            lane = ResumeLane(
                lane_id=lane_id,
                title=str(item.get("title") or lane_id),
                phase_id=str(item.get("phase_id") or "phase-00"),
                phase_index=int(item.get("phase_index") or 0),
                serialization_group=serialization_group,
                branch_name=str(item.get("branch_name") or ""),
                worktree_path=str(item.get("worktree_path") or ""),
                resume_bucket=resume_bucket,
                reason=reason,
                next_action=next_action,
                source_bucket=bucket,
                dependencies=deps,
                packet_path=str(resolved_packet_dir / "lanes" / lane_id / "resume.json") if resolved_packet_dir else None,
            )
            lanes.append(lane)
            if bucket == "complete":
                completed_source.add(lane_id)
            if resume_bucket == "relaunch-now":
                relaunch_now.append(lane_id)
                if serialization_group:
                    occupied_groups.add(serialization_group)
            elif resume_bucket == "waiting":
                waiting.append(lane_id)
            elif resume_bucket == "review-only":
                review.append(lane_id)
            else:
                done.append(lane_id)

        next_actions: list[str] = []
        if review:
            next_actions.append(f"Resolve review-only lanes before trusting another pass: {', '.join(review)}.")
        if relaunch_now:
            next_actions.append(f"Relaunch now in deterministic order: {', '.join(relaunch_now)}.")
        if waiting:
            next_actions.append(f"Keep these lanes waiting until prerequisites or earlier serialized relaunches finish: {', '.join(waiting)}.")
        if not next_actions:
            next_actions.append("No relaunch work remains. Preserve completed artifacts and continue with merge or closeout.")

        return ResumePlan(
            schema_version="agentkit.resume.v1",
            project_path=str(Path(reconcile.get("project_path") or root).expanduser().resolve()),
            target=str(reconcile.get("target") or "generic"),
            reconcile_path=str(resolved_reconcile_path),
            launch_path=str(launch_path),
            observe_path=str(observe_path) if observe_path else None,
            supervise_path=str(supervise_path) if supervise_path else None,
            relaunch_now_lane_ids=relaunch_now,
            waiting_lane_ids=waiting,
            review_lane_ids=review,
            completed_lane_ids=done,
            packet_dir=str(resolved_packet_dir) if resolved_packet_dir else None,
            next_actions=next_actions,
            lanes=lanes,
        )

    def render_markdown(self, plan: ResumePlan) -> str:
        lines = [
            f"# Resume plan: {Path(plan.project_path).name}",
            "",
            f"- Schema: `{plan.schema_version}`",
            f"- Project: `{plan.project_path}`",
            f"- Target: `{plan.target}`",
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
                    f"- Resume bucket: `{lane.resume_bucket}`",
                    f"- Source bucket: `{lane.source_bucket}`",
                    f"- Reason: {lane.reason}",
                    f"- Next action: {lane.next_action}",
                    f"- Serialization group: `{lane.serialization_group or 'none'}`",
                    f"- Worktree path: `{lane.worktree_path}`",
                    f"- Branch: `{lane.branch_name}`",
                ]
            )
            if lane.dependencies:
                lines.append("- Dependencies: " + ", ".join(f"{dep.lane_id} ({'satisfied' if dep.satisfied else 'pending'})" for dep in lane.dependencies))
            else:
                lines.append("- Dependencies: none")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def write_directory(self, plan: ResumePlan, output_dir: str | Path) -> Path:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "resume.md").write_text(self.render_markdown(plan), encoding="utf-8")
        (out / "resume.json").write_text(plan.to_json(), encoding="utf-8")
        lanes_dir = out / "lanes"
        for lane in plan.lanes:
            lane_dir = lanes_dir / lane.lane_id
            lane_dir.mkdir(parents=True, exist_ok=True)
            (lane_dir / "resume.json").write_text(json.dumps(lane.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (lane_dir / "resume.md").write_text(self._render_lane_markdown(lane), encoding="utf-8")
        return out

    def _render_lane_markdown(self, lane: ResumeLane) -> str:
        lines = [
            f"# Resume lane: {lane.lane_id}",
            "",
            f"- Resume bucket: `{lane.resume_bucket}`",
            f"- Source bucket: `{lane.source_bucket}`",
            f"- Reason: {lane.reason}",
            f"- Next action: {lane.next_action}",
            f"- Branch: `{lane.branch_name}`",
            f"- Worktree path: `{lane.worktree_path}`",
        ]
        return "\n".join(lines).rstrip() + "\n"

    def _resume_bucket(self, lane: dict[str, Any], deps: list[ResumeDependency], occupied_groups: set[str]) -> tuple[str, str, str]:
        bucket = str(lane.get("bucket") or "")
        lane_id = str(lane.get("lane_id") or "")
        group = str(lane.get("serialization_group") or "")
        if bucket == "complete":
            return "completed", str(lane.get("reason") or "Lane is already complete."), "Keep this lane closed unless a human explicitly reopens it."
        if bucket in {"blocked", "drifted", "needs-human-review", "still-running"}:
            return "review-only", str(lane.get("reason") or "Lane needs manual review."), str(lane.get("next_action") or "Inspect the lane manually before any relaunch.")
        if bucket == "waiting" or any(not dep.satisfied for dep in deps):
            return "waiting", str(lane.get("reason") or "Lane is still waiting on prerequisites."), str(lane.get("next_action") or "Finish earlier lanes first.")
        if bucket in {"ready", "relaunch-ready"}:
            if group and group in occupied_groups:
                return "waiting", f"Lane {lane_id} stays deferred so resume does not reopen serialization group {group!r} twice in the same pass.", "Relaunch the earlier lane in this serialization group first, then rebuild resume artifacts."
            return "relaunch-now", str(lane.get("reason") or "Lane is safe to relaunch now."), str(lane.get("next_action") or "Relaunch this lane now.")
        raise ResumeError(f"Saved reconcile artifact is contradictory: unsupported bucket {bucket!r} for lane {lane_id!r}.")

    def _load_reconcile(self, root: Path, *, reconcile_path: str | Path | None) -> tuple[Path, dict[str, Any]]:
        candidates = [Path(reconcile_path).expanduser().resolve()] if reconcile_path else [
            root / "reconcile.json",
            root / "reconcile" / "reconcile.json",
            root / "artifacts" / "reconcile.json",
            root / ".agentkit" / "reconcile.json",
        ]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate.resolve(), self._read_json(candidate)
        raise FileNotFoundError("No reconcile.json artifact found. Save a reconcile packet first, then run agentkit resume.")

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ResumeError(f"Saved resume evidence is malformed JSON: {path}") from exc
        if not isinstance(data, dict):
            raise ResumeError(f"Saved resume evidence must be a JSON object: {path}")
        return data

    def _require_file(self, path: Path, label: str) -> Path:
        value = str(path).strip()
        if not value:
            raise ResumeError(f"Saved reconcile artifact is incomplete: missing {label}.")
        if not path.exists() or not path.is_file():
            raise ResumeError(f"Saved reconcile artifact points at a missing {label}: {path}")
        return path.resolve()

    def _optional_file(self, path: Any) -> Path | None:
        value = str(path or "").strip()
        if not value:
            return None
        candidate = Path(value).expanduser().resolve()
        if not candidate.exists() or not candidate.is_file():
            raise ResumeError(f"Saved reconcile artifact points at a missing upstream artifact: {candidate}")
        return candidate

    def _validate_reconcile_shape(self, reconcile: dict[str, Any]) -> None:
        if str(reconcile.get("schema_version") or "") != "agentkit.reconcile.v1":
            raise ResumeError("Saved reconcile artifact is not a supported agentkit.reconcile.v1 packet.")
        lane_ids: set[str] = set()
        seen_in_summary: dict[str, set[str]] = {}
        for key in (
            "complete_lane_ids",
            "relaunch_ready_lane_ids",
            "ready_lane_ids",
            "still_running_lane_ids",
            "waiting_lane_ids",
            "blocked_lane_ids",
            "drifted_lane_ids",
            "needs_human_review_lane_ids",
        ):
            seen_in_summary[key] = {str(item) for item in reconcile.get(key) or []}
        for lane in reconcile.get("lanes") or []:
            lane_id = str(lane.get("lane_id") or "")
            bucket = str(lane.get("bucket") or "")
            if not lane_id or lane_id in lane_ids:
                raise ResumeError(f"Saved reconcile artifact is contradictory: duplicate or empty lane id {lane_id!r}.")
            lane_ids.add(lane_id)
            summary_key = {
                "complete": "complete_lane_ids",
                "relaunch-ready": "relaunch_ready_lane_ids",
                "ready": "ready_lane_ids",
                "still-running": "still_running_lane_ids",
                "waiting": "waiting_lane_ids",
                "blocked": "blocked_lane_ids",
                "drifted": "drifted_lane_ids",
                "needs-human-review": "needs_human_review_lane_ids",
            }.get(bucket)
            if summary_key is None or lane_id not in seen_in_summary[summary_key]:
                raise ResumeError(f"Saved reconcile artifact is contradictory: lane {lane_id!r} bucket {bucket!r} disagrees with summary ids.")
