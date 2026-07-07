from dataclasses import dataclass

from cleany_mission_manager.core.models import (
    MissionContext,
    MissionReport,
    MissionRequest,
)
from cleany_mission_manager.core.ports import Navigator, Perception, Planner, Reporter, SkillExecutor
from cleany_mission_manager.core.result import FailureCode, ModuleResult, ResultStatus
from cleany_mission_manager.core.states import MissionState


@dataclass(frozen=True)
class RetryPolicy:
    max_retries_per_state: int = 1
    max_retries_per_skill: int = 2


class MissionManager:
    def __init__(
        self,
        *,
        navigator: Navigator,
        perception: Perception,
        planner: Planner,
        skill_executor: SkillExecutor,
        reporter: Reporter,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.navigator = navigator
        self.perception = perception
        self.planner = planner
        self.skill_executor = skill_executor
        self.reporter = reporter
        self.retry_policy = retry_policy or RetryPolicy()
        self.context = MissionContext()

    @property
    def state(self) -> MissionState:
        return self.context.state

    def start(self, request: MissionRequest) -> None:
        if self.state != MissionState.IDLE:
            raise RuntimeError(f"Cannot start mission from state {self.state}")
        self.context = MissionContext(request=request, state=MissionState.NAVIGATE_TO_TARGET)

    def reset(self) -> None:
        if self.state != MissionState.ERROR:
            raise RuntimeError(f"Cannot reset from state {self.state}; reset() is only valid from ERROR")
        self.context = MissionContext()

    def run_until_idle_or_error(self) -> MissionReport | None:
        while self.state not in (MissionState.IDLE, MissionState.ERROR):
            self.step()
        return self.context.report

    def step(self) -> None:
        if self.context.request is None:
            return

        match self.state:
            case MissionState.NAVIGATE_TO_TARGET:
                result = self.navigator.navigate_to_target(self.context.request)
                self._handle_navigation_result(result, MissionState.PERCEIVE)
            case MissionState.PERCEIVE:
                result = self.perception.perceive(self.context.request)
                self._handle_perception_result(result)
            case MissionState.PLAN_TASKS:
                result = self.planner.plan(self.context.world_state)
                self._handle_plan_result(result)
            case MissionState.EXECUTE_TASKS:
                self._execute_next_skill()
            case MissionState.RETURN_HOME:
                result = self.navigator.return_home(self.context.request)
                self._handle_navigation_result(result, MissionState.REPORT)
            case MissionState.REPORT:
                self._publish_report()
                self.context.state = MissionState.IDLE
            case MissionState.ERROR | MissionState.IDLE:
                return

    def _skill_sequence(self) -> list[object]:
        plan = self.context.plan or {}
        if isinstance(plan, dict):
            return list(plan.get("skill_sequence", []))
        return []

    def _execute_next_skill(self) -> None:
        skill_sequence = self._skill_sequence()
        if self.context.next_skill_index >= len(skill_sequence):
            self.context.state = MissionState.RETURN_HOME
            return

        skill = skill_sequence[self.context.next_skill_index]
        skill_name = skill.get("skill") if isinstance(skill, dict) else str(skill)
        result = self.skill_executor.execute_skill(skill)

        if result.status == ResultStatus.OK:
            self.context.completed_skills.append(skill_name)
            self.context.next_skill_index += 1
            if self.context.next_skill_index >= len(skill_sequence):
                self.context.state = MissionState.RETURN_HOME
            return

        self._handle_non_ok_result(
            result,
            retry_key=f"skill:{self.context.next_skill_index}",
            retry_limit=self.retry_policy.max_retries_per_skill,
            failed_task=skill_name,
        )

    def _handle_navigation_result(
        self,
        result: ModuleResult[object],
        success_state: MissionState,
    ) -> None:
        if result.status == ResultStatus.OK:
            self.context.state = success_state
            return
        self._handle_non_ok_result(result, retry_key=str(self.state), failed_task=self.state.name)

    def _handle_perception_result(self, result: ModuleResult[object]) -> None:
        if result.status == ResultStatus.OK:
            self.context.world_state = result.data
            self.context.state = MissionState.PLAN_TASKS
            return
        self._handle_non_ok_result(result, retry_key=str(self.state), failed_task=self.state.name)

    def _handle_plan_result(self, result: ModuleResult[object]) -> None:
        if result.status == ResultStatus.OK:
            self.context.plan = result.data
            self._record_non_actionable_tasks(result.data)
            self.context.state = MissionState.EXECUTE_TASKS
            return
        self._handle_non_ok_result(result, retry_key=str(self.state), failed_task=self.state.name)

    def _record_non_actionable_tasks(self, plan: object) -> None:
        if not isinstance(plan, dict):
            return
        for task in plan.get("tasks", []):
            if not isinstance(task, dict):
                continue
            action = task.get("action")
            if action == "human_review":
                self.context.needs_human_review = True
                self.context.skipped_tasks.append(task.get("task_id", action))
            elif action == "skip":
                self.context.skipped_tasks.append(task.get("task_id", action))

    def _handle_non_ok_result(
        self,
        result: ModuleResult[object],
        *,
        retry_key: str,
        retry_limit: int | None = None,
        failed_task: str | None = None,
    ) -> None:
        if result.status == ResultStatus.FATAL:
            self.context.report = self._make_report("FAILED", result, failed_task=failed_task)
            self.reporter.publish(self.context.report)
            self.context.state = MissionState.ERROR
            return

        if result.status == ResultStatus.BLOCKED:
            self.context.report = self._make_report("BLOCKED", result, failed_task=failed_task)
            self.context.state = MissionState.REPORT
            return

        limit = retry_limit if retry_limit is not None else self.retry_policy.max_retries_per_state
        if result.status == ResultStatus.FAILED and result.retryable and self._can_retry(retry_key, limit):
            self._record_retry(retry_key)
            return

        self.context.report = self._make_report("FAILED", result, failed_task=failed_task)
        self.context.state = MissionState.REPORT

    def _can_retry(self, key: str, limit: int) -> bool:
        return self.context.retry_counts.get(key, 0) < limit

    def _record_retry(self, key: str) -> None:
        self.context.retry_counts[key] = self.context.retry_counts.get(key, 0) + 1

    def _publish_report(self) -> None:
        if self.context.report is None:
            self.context.report = self._make_report(self._success_status())
        self.reporter.publish(self.context.report)

    def _success_status(self) -> str:
        if self.context.needs_human_review:
            return "HUMAN_REVIEW_REQUIRED"
        if self.context.skipped_tasks:
            return "PARTIAL_SUCCESS"
        return "SUCCESS"

    def _make_report(
        self,
        status: str,
        result: ModuleResult[object] | None = None,
        *,
        failed_task: str | None = None,
    ) -> MissionReport:
        request = self.context.request
        mission_id = request.mission_id if request else "unknown"
        failure_code: FailureCode | None = result.failure_code if result else None
        message = result.message if result else "Mission completed successfully."
        return MissionReport(
            mission_id=mission_id,
            status=status,
            failure_code=failure_code,
            summary=message,
            completed_tasks=list(self.context.completed_skills),
            skipped_tasks=list(self.context.skipped_tasks),
            needs_human_review=self.context.needs_human_review,
            failed_task=failed_task,
        )
