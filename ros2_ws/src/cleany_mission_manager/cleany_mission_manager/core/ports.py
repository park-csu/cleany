from typing import Any, Protocol

from cleany_mission_manager.core.models import MissionRequest
from cleany_mission_manager.core.result import ModuleResult


class Navigator(Protocol):
    def navigate_to_target(self, request: MissionRequest) -> ModuleResult[Any]:
        ...

    def return_home(self, request: MissionRequest) -> ModuleResult[Any]:
        ...


class Perception(Protocol):
    def perceive(self, request: MissionRequest) -> ModuleResult[Any]:
        ...


class Planner(Protocol):
    def plan(self, world_state: Any) -> ModuleResult[Any]:
        ...


class SkillExecutor(Protocol):
    def execute(self, plan: Any) -> ModuleResult[Any]:
        ...


class Reporter(Protocol):
    def publish(self, report: Any) -> None:
        ...
