from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


@dataclass
class BurnToolUse:
    name: str
    call_count: int = 1
    duration_ms: Optional[int] = None


@dataclass
class BurnCost:
    amount_usd: Optional[float]
    state: str
    estimated: bool = False
    currency: str = "USD"


@dataclass
class BurnTurn:
    turn_id: str
    role: str
    model: str
    provider: str
    task_label: str
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    tool_uses: list[BurnToolUse] = field(default_factory=list)
    cost: BurnCost = field(default_factory=lambda: BurnCost(amount_usd=None, state="unknown"))
    timestamp: Optional[str] = None
    project_root: Optional[str] = None
    source: Optional[str] = None


@dataclass
class BurnSession:
    session_id: str
    source: str
    provider: str
    model: str
    project_root: Optional[str]
    task_label: str
    started_at: Optional[str]
    ended_at: Optional[str]
    turns: list[BurnTurn] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "source": self.source,
            "provider": self.provider,
            "model": self.model,
            "project_root": self.project_root,
            "task_label": self.task_label,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "turns": [
                {
                    **asdict(turn),
                    "tool_uses": [asdict(tool) for tool in turn.tool_uses],
                    "cost": asdict(turn.cost),
                }
                for turn in self.turns
            ],
        }


class BurnAdapterError(ValueError):
    pass


KNOWN_PROJECT_KEYS = ("project_root", "cwd", "workspace", "repo_path", "project")
KNOWN_TASK_KEYS = ("task_label", "label", "task", "title", "prompt_summary")
KNOWN_MODEL_KEYS = ("model", "model_name")
KNOWN_PROVIDER_KEYS = ("provider", "vendor")
KNOWN_COST_KEYS = ("cost_usd", "cost", "usd")


def load_sessions(path: Path | str) -> list[BurnSession]:
    root = Path(path)
    files: list[Path] = []
    if root.is_file():
        files = [root]
    elif root.exists():
        files = sorted(p for p in root.rglob("*") if p.is_file())
    sessions: list[BurnSession] = []
    for candidate in files:
        adapter = detect_adapter(candidate)
        if not adapter:
            continue
        sessions.extend(adapter(candidate))
    return sorted(sessions, key=lambda s: (s.started_at or "", s.session_id))


def detect_adapter(path: Path):
    name = path.name.lower()
    if name.endswith(".codex.json"):
        return parse_codex_file
    if name.endswith(".claude.json"):
        return parse_claude_file
    if name.endswith(".openclaw.jsonl"):
        return parse_openclaw_file
    return None


def parse_codex_file(path: Path) -> list[BurnSession]:
    payload = _read_json(path)
    if "session_id" not in payload or "turns" not in payload:
        raise BurnAdapterError(f"Malformed Codex transcript: {path}")
    turns = [_normalize_turn(item, default_source="codex", session=payload) for item in payload.get("turns", [])]
    return [
        BurnSession(
            session_id=str(payload["session_id"]),
            source="codex",
            provider=str(payload.get("provider") or "openai"),
            model=str(payload.get("model") or _session_model(turns)),
            project_root=_session_project(payload, turns),
            task_label=str(payload.get("task_label") or payload.get("task") or _session_task(turns)),
            started_at=_iso(payload.get("started_at")),
            ended_at=_iso(payload.get("ended_at")),
            turns=turns,
        )
    ]


def parse_claude_file(path: Path) -> list[BurnSession]:
    payload = _read_json(path)
    if "id" not in payload or "messages" not in payload:
        raise BurnAdapterError(f"Malformed Claude transcript: {path}")
    session_meta = {
        "provider": payload.get("provider") or "anthropic",
        "model": payload.get("model"),
        "project_root": payload.get("workspace"),
        "task_label": payload.get("task") or payload.get("title"),
    }
    turns = [_normalize_turn(item, default_source="claude-code", session=session_meta) for item in payload.get("messages", [])]
    return [
        BurnSession(
            session_id=str(payload["id"]),
            source="claude-code",
            provider=str(session_meta["provider"]),
            model=str(payload.get("model") or _session_model(turns)),
            project_root=_session_project(session_meta, turns),
            task_label=str(session_meta.get("task_label") or _session_task(turns)),
            started_at=_iso(payload.get("started_at")),
            ended_at=_iso(payload.get("ended_at")),
            turns=turns,
        )
    ]


def parse_openclaw_file(path: Path) -> list[BurnSession]:
    records = _read_jsonl(path)
    if not records:
        raise BurnAdapterError(f"Malformed OpenClaw transcript: {path}")
    sessions: dict[str, list[dict[str, Any]]] = {}
    metas: dict[str, dict[str, Any]] = {}
    for record in records:
        session_id = str(record.get("session_id") or record.get("conversation_id") or "")
        if not session_id:
            raise BurnAdapterError(f"OpenClaw record missing session_id: {path}")
        sessions.setdefault(session_id, []).append(record)
        metas.setdefault(session_id, record)
    result: list[BurnSession] = []
    for session_id, items in sorted(sessions.items()):
        turns = [_normalize_turn(item, default_source="openclaw", session=metas[session_id]) for item in items]
        timestamps = [t.timestamp for t in turns if t.timestamp]
        result.append(
            BurnSession(
                session_id=session_id,
                source="openclaw",
                provider=str(metas[session_id].get("provider") or _session_provider(turns)),
                model=str(metas[session_id].get("model") or _session_model(turns)),
                project_root=_session_project(metas[session_id], turns),
                task_label=str(metas[session_id].get("task_label") or _session_task(turns)),
                started_at=min(timestamps) if timestamps else None,
                ended_at=max(timestamps) if timestamps else None,
                turns=turns,
            )
        )
    return result


def _normalize_turn(item: dict[str, Any], default_source: str, session: dict[str, Any]) -> BurnTurn:
    model = _pick(item, KNOWN_MODEL_KEYS) or _pick(session, KNOWN_MODEL_KEYS) or "unknown"
    provider = _pick(item, KNOWN_PROVIDER_KEYS) or _pick(session, KNOWN_PROVIDER_KEYS) or _provider_from_model(model)
    raw_tools = item.get("tool_uses") or item.get("tools") or item.get("tool_calls") or []
    tool_uses = _normalize_tools(raw_tools)
    amount, state, estimated = _normalize_cost(item)
    return BurnTurn(
        turn_id=str(item.get("turn_id") or item.get("id") or item.get("message_id") or f"turn-{abs(hash(json.dumps(item, sort_keys=True, default=str)))}"),
        role=str(item.get("role") or item.get("sender") or "assistant"),
        model=str(model),
        provider=str(provider or "unknown"),
        task_label=str(_pick(item, KNOWN_TASK_KEYS) or _pick(session, KNOWN_TASK_KEYS) or "unlabeled"),
        input_tokens=_intish(item.get("input_tokens") or item.get("prompt_tokens")),
        output_tokens=_intish(item.get("output_tokens") or item.get("completion_tokens")),
        tool_uses=tool_uses,
        cost=BurnCost(amount_usd=amount, state=state, estimated=estimated),
        timestamp=_iso(item.get("timestamp") or item.get("ts") or item.get("created_at")),
        project_root=_pick(item, KNOWN_PROJECT_KEYS) or _pick(session, KNOWN_PROJECT_KEYS),
        source=default_source,
    )


def _normalize_tools(raw_tools: Any) -> list[BurnToolUse]:
    result: list[BurnToolUse] = []
    if not isinstance(raw_tools, list):
        return result
    for entry in raw_tools:
        if isinstance(entry, str):
            result.append(BurnToolUse(name=entry))
        elif isinstance(entry, dict):
            result.append(
                BurnToolUse(
                    name=str(entry.get("name") or entry.get("tool") or "unknown-tool"),
                    call_count=_intish(entry.get("count")) or 1,
                    duration_ms=_intish(entry.get("duration_ms") or entry.get("latency_ms")),
                )
            )
    return result


def _normalize_cost(item: dict[str, Any]) -> tuple[Optional[float], str, bool]:
    if "cost_state" in item and item.get("cost_state") == "unknown":
        return None, "unknown", False
    for key in KNOWN_COST_KEYS:
        if key in item:
            raw = item.get(key)
            if raw is None:
                return None, "missing", False
            try:
                return round(float(raw), 6), "actual", False
            except (TypeError, ValueError):
                return None, "unknown", False
    total = None
    pricing = item.get("pricing") if isinstance(item.get("pricing"), dict) else None
    if pricing and ("input_per_1k" in pricing or "output_per_1k" in pricing):
        in_tok = _intish(item.get("input_tokens") or item.get("prompt_tokens")) or 0
        out_tok = _intish(item.get("output_tokens") or item.get("completion_tokens")) or 0
        total = (in_tok / 1000.0) * float(pricing.get("input_per_1k") or 0) + (out_tok / 1000.0) * float(pricing.get("output_per_1k") or 0)
        return round(total, 6), "estimated", True
    return None, "unknown", False


def _session_project(meta: dict[str, Any], turns: Iterable[BurnTurn]) -> Optional[str]:
    return _pick(meta, KNOWN_PROJECT_KEYS) or next((t.project_root for t in turns if t.project_root), None)


def _session_task(turns: Iterable[BurnTurn]) -> str:
    return next((t.task_label for t in turns if t.task_label and t.task_label != "unlabeled"), "unlabeled")


def _session_model(turns: Iterable[BurnTurn]) -> str:
    return next((t.model for t in turns if t.model and t.model != "unknown"), "unknown")


def _session_provider(turns: Iterable[BurnTurn]) -> str:
    return next((t.provider for t in turns if t.provider and t.provider != "unknown"), "unknown")


def _pick(payload: dict[str, Any], keys: Iterable[str]) -> Optional[str]:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def _intish(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _provider_from_model(model: str) -> str:
    lowered = str(model).lower()
    if "claude" in lowered:
        return "anthropic"
    if "gpt" in lowered or "o1" in lowered or "o3" in lowered:
        return "openai"
    return "unknown"


def _iso(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return text


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BurnAdapterError(f"Malformed JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BurnAdapterError(f"Expected object in {path}")
    return data


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BurnAdapterError(f"Malformed JSONL in {path} line {line_no}: {exc}") from exc
        if not isinstance(record, dict):
            raise BurnAdapterError(f"Expected object in {path} line {line_no}")
        records.append(record)
    return records
