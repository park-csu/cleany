import pytest

from cleany_mission_manager.core.manager import MissionManager
from cleany_mission_manager.core.models import MissionRequest
from cleany_mission_manager.core.result import FailureCode, ModuleResult
from cleany_mission_manager.core.states import MissionState
from cleany_mission_manager.mocks.components import (
    InMemoryReporter,
    MockNavigator,
    MockPerception,
    MockPlanner,
    MockSkillExecutor,
    ScriptedNavigator,
    ScriptedPerception,
    ScriptedPlanner,
)


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
    navigator = ScriptedNavigator(
        target_results=[ModuleResult.fatal(FailureCode.HARDWARE_ERROR, message="hardware fault")]
    )
    manager = MissionManager(
        navigator=navigator,
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


def _start(manager: MissionManager, mission_id: str = "mission_x") -> None:
    manager.start(
        MissionRequest(
            mission_id=mission_id,
            mission_type="clean_seat",
            target_id="seat_A_12",
            requested_by="dashboard",
        )
    )


def test_retryable_failure_recovers_on_next_attempt() -> None:
    navigator = ScriptedNavigator(
        target_results=[
            ModuleResult.failed(FailureCode.NAVIGATION_FAIL, retryable=True, message="transient glitch"),
            ModuleResult.success({"reached": True}, "navigation succeeded"),
        ]
    )
    reporter = InMemoryReporter()
    manager = MissionManager(
        navigator=navigator,
        perception=MockPerception(),
        planner=MockPlanner(),
        skill_executor=MockSkillExecutor(),
        reporter=reporter,
    )

    _start(manager)
    report = manager.run_until_idle_or_error()

    assert navigator._navigate.call_count == 2
    assert manager.state == MissionState.IDLE
    assert report is not None
    assert report.status == "SUCCESS"


def test_retryable_failure_exhausts_retries_and_reports_failed() -> None:
    navigator = ScriptedNavigator(
        target_results=[
            ModuleResult.failed(FailureCode.NAVIGATION_FAIL, retryable=True, message="glitch 1"),
            ModuleResult.failed(FailureCode.NAVIGATION_FAIL, retryable=True, message="glitch 2"),
        ]
    )
    reporter = InMemoryReporter()
    manager = MissionManager(
        navigator=navigator,
        perception=MockPerception(),
        planner=MockPlanner(),
        skill_executor=MockSkillExecutor(),
        reporter=reporter,
    )

    _start(manager)
    report = manager.run_until_idle_or_error()

    assert navigator._navigate.call_count == 2
    assert manager.state == MissionState.IDLE
    assert report is not None
    assert report.status == "FAILED"
    assert report.failure_code == FailureCode.NAVIGATION_FAIL
    assert len(reporter.reports) == 1


def test_blocked_plan_reports_blocked_without_executing_skills() -> None:
    planner = ScriptedPlanner(
        [ModuleResult.blocked(FailureCode.PLAN_BLOCKED, message="all detected objects are unreachable")]
    )
    reporter = InMemoryReporter()
    manager = MissionManager(
        navigator=MockNavigator(),
        perception=MockPerception(),
        planner=planner,
        skill_executor=MockSkillExecutor(),
        reporter=reporter,
    )

    _start(manager)
    report = manager.run_until_idle_or_error()

    assert manager.state == MissionState.IDLE
    assert report is not None
    assert report.status == "BLOCKED"
    assert report.failure_code == FailureCode.PLAN_BLOCKED
    assert report.completed_tasks == []


def test_no_objects_detected_reports_blocked_without_planning() -> None:
    perception = ScriptedPerception([ModuleResult.blocked(FailureCode.NO_OBJECTS, message="nothing to clean")])
    planner = ScriptedPlanner([ModuleResult.success({"tasks": []}, "unused")])
    reporter = InMemoryReporter()
    manager = MissionManager(
        navigator=MockNavigator(),
        perception=perception,
        planner=planner,
        skill_executor=MockSkillExecutor(),
        reporter=reporter,
    )

    _start(manager)
    report = manager.run_until_idle_or_error()

    assert planner._plan.call_count == 0
    assert manager.state == MissionState.IDLE
    assert report is not None
    assert report.status == "BLOCKED"
    assert report.failure_code == FailureCode.NO_OBJECTS
