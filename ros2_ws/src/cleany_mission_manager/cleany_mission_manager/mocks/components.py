from typing import Any

from cleany_mission_manager.core.models import MissionReport, MissionRequest
from cleany_mission_manager.core.result import ModuleResult


class MockNavigator:
    def navigate_to_target(self, request: MissionRequest) -> ModuleResult[dict[str, Any]]:
        return ModuleResult.success(
            {
                "target_id": request.target_id,
                "reached": True,
                "current_pose": "mock_target_pose",
            },
            "navigation succeeded",
        )

    def return_home(self, request: MissionRequest) -> ModuleResult[dict[str, Any]]:
        return ModuleResult.success(
            {
                "target_id": "home",
                "reached": True,
                "current_pose": "mock_home_pose",
            },
            "return home succeeded",
        )


class MockPerception:
    def perceive(self, request: MissionRequest) -> ModuleResult[dict[str, Any]]:
        return ModuleResult.success(
            {
                "objects": [
                    {
                        "object_id": "obj_1",
                        "class_name": "trash",
                        "confidence": 0.92,
                    }
                ],
                "snapshot_id": "snapshot_001",
            },
            "objects detected",
        )


class MockPlanner:
    def plan(self, world_state: Any) -> ModuleResult[dict[str, Any]]:
        return ModuleResult.success(
            {
                "tasks": [
                    {
                        "task_id": "task_1",
                        "action": "collect",
                        "object_id": "obj_1",
                    }
                ],
                "skill_sequence": [
                    {"skill": "pick_object", "args": {"object_id": "obj_1"}},
                    {"skill": "place_object", "args": {"target": "trash_bin"}},
                ],
            },
            "plan created",
        )


class MockSkillExecutor:
    def execute(self, plan: Any) -> ModuleResult[dict[str, Any]]:
        return ModuleResult.success(
            {
                "completed_skills": ["pick_object", "place_object"],
                "failed_skill": None,
            },
            "skills executed",
        )


class InMemoryReporter:
    def __init__(self) -> None:
        self.reports: list[MissionReport] = []

    def publish(self, report: MissionReport) -> None:
        self.reports.append(report)
