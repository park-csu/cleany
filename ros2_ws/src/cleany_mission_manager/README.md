# cleany_mission_manager

Mission Manager FSM과 mission lifecycle을 담당하는 ROS 2 패키지.

초기 FSM은 `IDLE -> NAVIGATE_TO_TARGET -> PERCEIVE -> PLAN_TASKS -> EXECUTE_TASKS -> RETURN_HOME -> REPORT` 흐름을 기준으로 구현한다.
상세 설계 초안은 `DESIGN.md`를 참고한다.
이전 설계 초안과 결정 메모는 `notes/` 아래에 보존한다.
