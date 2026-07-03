# Mission Manager Decisions

이 문서는 Mission Manager 설계 논의에서 확정한 내용을 짧게 기록한다.
상세 설계 본문은 `DESIGN.md`를 참고한다.

## Core Principle

FSM은 끝까지 유지하고, Planner만 교체 가능하게 만든다.

## FSM Boundary

- FSM은 VLM/VLA가 생성하거나 수정하지 않는다.
- VLM/VLA는 `PLAN_TASKS` 상태 안에서 고수준 작업 계획만 담당한다.
- timeout, retry, stop/reset, error recovery, logging은 Mission Manager FSM이 담당한다.
- 실제 인식, 계획, 실행 구현은 interface 뒤에 둔다.

## VLM/VLA Role

VLM/VLA가 결정할 수 있는 것:

- 어떤 작업을 수행할지
- 어떤 객체를 target으로 삼을지
- 어떤 skill을 어떤 순서로 호출할지
- 애매한 객체를 skip 또는 human review 대상으로 둘지

VLM/VLA가 직접 결정하지 않는 것:

- FSM 상태 전이
- retry / timeout 정책
- emergency stop 이후 처리
- error recovery
- 최종 실행 승인

## MVP FSM States

퇴실 좌석 정리 시나리오의 MVP FSM은 다음 8개 상태로 시작한다.

```text
IDLE
NAVIGATE_TO_TARGET
PERCEIVE
PLAN_TASKS
EXECUTE_TASKS
RETURN_HOME
REPORT
ERROR
```

흐름:

```text
IDLE
  -> NAVIGATE_TO_TARGET
  -> PERCEIVE
  -> PLAN_TASKS
  -> EXECUTE_TASKS
  -> RETURN_HOME
  -> REPORT
  -> IDLE

Any state -> ERROR
```

나중에 필요해지면 `PERCEIVE`, `EXECUTE_TASKS`, `REPORT`를 더 작은 상태로 분해한다.

## Implementation Order

첫 구현은 다음 순서로 진행한다.

1. ROS2에 의존하지 않는 FSM core 작성
2. `MissionState`, `MissionContext`, `FailureCode` 정의
3. `Planner` interface와 `RuleBasedPlanner` 작성
4. Mock perception / mock skill executor로 성공 시나리오 검증
5. pytest로 `IDLE -> NAVIGATE_TO_TARGET -> PERCEIVE -> PLAN_TASKS -> EXECUTE_TASKS -> RETURN_HOME -> REPORT` 검증
6. 이후 ROS2 node wrapper 작성
