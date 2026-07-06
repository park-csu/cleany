import pytest

from cleany_mission_manager.core.manager import MissionManager
from cleany_mission_manager.core.models import MissionRequest
from cleany_mission_manager.core.result import FailureCode, ModuleResult, ResultStatus
from cleany_mission_manager.core.states import MissionState
from cleany_mission_manager.mocks.components import (
    InMemoryReporter,
    MockNavigator,
    MockPerception,
    MockPlanner,
    MockSkillExecutor,
)


class FatalNavigator:
    def navigate_to_target(self, request: MissionRequest) -> ModuleResult[dict]:
        return ModuleResult(
            ok=False,
            status=ResultStatus.FATAL,
            failure_code=FailureCode.HARDWARE_ERROR,
            message="hardware fault",
        )

    def return_home(self, request: MissionRequest) -> ModuleResult[dict]:
        raise AssertionError("return_home should not be called after a FATAL navigation result")


def test_successful_mock_mission_flow_returns_to_idle() -> None:
    reporter = InMemoryReporter()
    manager = MissionManager(
        navigator=MockNavigator(),
        perception=MockPerception(),
        planner=MockPlanner(),
        skill_executor=MockSkillExecutor(),
        reporter=reporter,
    )

    manager.start(
        MissionRequest(
            mission_id="mission_001",
            mission_type="clean_seat",
            target_id="seat_A_12",
            requested_by="dashboard",
        )
    )

    report = manager.run_until_idle_or_error()

    assert manager.state == MissionState.IDLE
    assert report is not None
    assert report.status == "SUCCESS"
    assert report.completed_tasks == ["pick_object", "place_object"]
    assert len(reporter.reports) == 1


def test_fatal_result_moves_to_error_and_reset_returns_to_idle() -> None:
    reporter = InMemoryReporter()
    manager = MissionManager(
        navigator=FatalNavigator(),
        perception=MockPerception(),
        planner=MockPlanner(),
        skill_executor=MockSkillExecutor(),
        reporter=reporter,
    )

    manager.start(
        MissionRequest(
            mission_id="mission_002",
            mission_type="clean_seat",
            target_id="seat_A_12",
            requested_by="dashboard",
        )
    )
    report = manager.run_until_idle_or_error()

    assert manager.state == MissionState.ERROR
    assert report is not None
    assert report.status == "FAILED"
    assert report.failure_code == FailureCode.HARDWARE_ERROR
    assert len(reporter.reports) == 1

    manager.reset()

    assert manager.state == MissionState.IDLE

    manager.start(
        MissionRequest(
            mission_id="mission_003",
            mission_type="clean_seat",
            target_id="seat_A_12",
            requested_by="dashboard",
        )
    )
    with pytest.raises(RuntimeError):
        manager.reset()


def test_reset_from_idle_is_rejected() -> None:
    manager = MissionManager(
        navigator=MockNavigator(),
        perception=MockPerception(),
        planner=MockPlanner(),
        skill_executor=MockSkillExecutor(),
        reporter=InMemoryReporter(),
    )

    with pytest.raises(RuntimeError):
        manager.reset()
