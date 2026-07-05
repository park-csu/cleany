from cleany_mission_manager.core.manager import MissionManager
from cleany_mission_manager.core.models import MissionRequest
from cleany_mission_manager.core.states import MissionState
from cleany_mission_manager.mocks.components import (
    InMemoryReporter,
    MockNavigator,
    MockPerception,
    MockPlanner,
    MockSkillExecutor,
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
