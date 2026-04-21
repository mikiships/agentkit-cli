from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class ResumeDependency:
    lane_id: str
    reason: str
    satisfied: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ResumeLane:
    lane_id: str
    title: str
    phase_id: str
    phase_index: int
    serialization_group: str
    branch_name: str
    worktree_path: str
    resume_bucket: str
    reason: str
    next_action: str
    source_bucket: str
    dependencies: list[ResumeDependency] = field(default_factory=list)
    packet_path: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["dependencies"] = [item.to_dict() for item in self.dependencies]
        return payload


@dataclass(frozen=True)
class ResumePlan:
    schema_version: str
    project_path: str
    target: str
    reconcile_path: str
    launch_path: str
    observe_path: str | None
    supervise_path: str | None
    relaunch_now_lane_ids: list[str] = field(default_factory=list)
    waiting_lane_ids: list[str] = field(default_factory=list)
    review_lane_ids: list[str] = field(default_factory=list)
    completed_lane_ids: list[str] = field(default_factory=list)
    packet_dir: str | None = None
    next_actions: list[str] = field(default_factory=list)
    lanes: list[ResumeLane] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["lanes"] = [item.to_dict() for item in self.lanes]
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)
