# Cleany Mission Manager Design

이 문서는 Cleany Mission Manager의 설계를 처음부터 다시 정리하기 위한 작업 문서다.

기존 초안은 `notes/DESIGN.old.md`에 보존한다.
기존 결정 메모는 `notes/DECISIONS.old.md`에 보존한다.

## Goal

Mission Manager는 퇴실 좌석 정리 mission의 전체 흐름을 FSM으로 관리한다.

Mission Manager는 외부 요청을 받아 목표 위치로 이동하고, perception, planner, skill executor를 순서대로 호출하며, 각 모듈의 결과를 바탕으로 다음 상태를 결정한다.

다른 모듈은 event 또는 result를 반환할 수 있지만, Mission Manager의 상태를 직접 변경하지 않는다.
FSM 상태 전이 권한은 Mission Manager에만 있다.

Mission Manager가 직접 책임지지 않는 것:

- 퇴실 여부 자체 판단
- 객체 탐지 모델 실행
- task plan 생성
- skill 내부 로봇 제어
- low-level safety 계산

MVP에서는 Safety Supervisor 또는 Safety Guardrail을 독립 컴포넌트로 두지 않는다.
각 모듈이 자기 책임 범위의 기본 safety check를 수행하고, Mission Manager는 공통 result를 해석해 상태를 전이한다.

## Mission Scenario

TODO

## FSM States

초기 MVP FSM은 다음 8개 상태로 시작한다.

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

## State Responsibilities

TODO

## Inputs and Outputs

TODO

## Planner Boundary

Planner는 현재 world state를 보고 수행할 task와 skill sequence를 제안한다.

Planner는 `collect`, `skip`, `store_lost_item`, `human_review` 같은 판단을 반환할 수 있다.
하지만 Planner가 FSM 상태 전이를 직접 발생시키지는 않는다.

상태 전이 권한은 Mission Manager에만 있다.

## Execution Boundary

Skill Executor는 Mission Manager가 요청한 skill을 실행하고 결과를 반환한다.

Skill Executor는 skill 내부에서 필요한 기본 safety check를 수행할 수 있다.
예를 들어 timeout, grasp failure, collision risk, e-stop 같은 결과를 반환할 수 있다.

하지만 Skill Executor가 Mission Manager의 상태를 직접 변경하지는 않는다.
Mission Manager는 Skill Executor의 result를 해석해 retry, report, error 전이를 결정한다.

## Open Questions

TODO
