from dataclasses import dataclass, field
from typing import Any

from cleany_mission_manager.core.result import FailureCode
from cleany_mission_manager.core.states import MissionState


@dataclass(frozen=True)
class MissionRequest:
    mission_id: str
    mission_type: str
    target_id: str
    requested_by: str


@dataclass
class MissionReport:
    mission_id: str
    status: str
    failure_code: FailureCode | None = None
    summary: str = ""
    completed_tasks: list[str] = field(default_factory=list)
    skipped_tasks: list[str] = field(default_factory=list)
    failed_task: str | None = None
    needs_human_review: bool = False


@dataclass
class MissionContext:
    request: MissionRequest | None = None
    state: MissionState = MissionState.IDLE
    retry_counts: dict[str, int] = field(default_factory=dict)
    world_state: Any | None = None
    plan: Any | None = None
    completed_skills: list[str] = field(default_factory=list)
    report: MissionReport | None = None
