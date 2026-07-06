from typing import Any, Sequence

from cleany_mission_manager.core.models import MissionReport, MissionRequest
from cleany_mission_manager.core.result import ModuleResult


class _ScriptedCalls:
    """Returns queued results in order, repeating the last one once exhausted."""

    def __init__(self, results: Sequence[ModuleResult[Any]]) -> None:
        if not results:
            raise ValueError("ScriptedCalls requires at least one result")
        self._results = list(results)
        self.call_count = 0

    def __call__(self) -> ModuleResult[Any]:
        self.call_count += 1
        if len(self._results) > 1:
            return self._results.pop(0)
        return self._results[0]


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
    def execute_skill(self, skill: Any) -> ModuleResult[dict[str, Any]]:
        return ModuleResult.success(message="skill executed")


class ScriptedNavigator:
    def __init__(
        self,
        target_results: Sequence[ModuleResult[Any]],
        home_results: Sequence[ModuleResult[Any]] | None = None,
    ) -> None:
        self._navigate = _ScriptedCalls(target_results)
        self._return_home = _ScriptedCalls(
            home_results or [ModuleResult.success({"reached": True}, "return home succeeded")]
        )

    def navigate_to_target(self, request: MissionRequest) -> ModuleResult[Any]:
        return self._navigate()

    def return_home(self, request: MissionRequest) -> ModuleResult[Any]:
        return self._return_home()


class ScriptedPerception:
    def __init__(self, results: Sequence[ModuleResult[Any]]) -> None:
        self._perceive = _ScriptedCalls(results)

    def perceive(self, request: MissionRequest) -> ModuleResult[Any]:
        return self._perceive()


class ScriptedPlanner:
    def __init__(self, results: Sequence[ModuleResult[Any]]) -> None:
        self._plan = _ScriptedCalls(results)

    def plan(self, world_state: Any) -> ModuleResult[Any]:
        return self._plan()


class ScriptedSkillExecutor:
    def __init__(self, results: Sequence[ModuleResult[Any]]) -> None:
        self._execute_skill = _ScriptedCalls(results)
        self.skills_seen: list[Any] = []

    def execute_skill(self, skill: Any) -> ModuleResult[Any]:
        self.skills_seen.append(skill)
        return self._execute_skill()


class InMemoryReporter:
    def __init__(self) -> None:
        self.reports: list[MissionReport] = []

    def publish(self, report: MissionReport) -> None:
        self.reports.append(report)
