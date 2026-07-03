# Cleany Mission Manager 설계 초안

## 1. 목적

이 문서는 Cleany 프로젝트의 **Mission Manager / FSM / Planner 교체 구조**를 정리하기 위한 초기 설계 문서이다.

Cleany는 무인 스터디카페, 독서실, 공유오피스와 같은 무인 공간에서 퇴실 후 정리 작업을 수행하는 Physical AI 로봇이다. 로봇은 카메라와 RGB-D, LiDAR, IMU 등의 센서로 공간 상태를 인식하고, Jetson AGX Orin에서 온디바이스 추론을 수행한 뒤, ROS2 기반 제어 계층을 통해 이동·파지·정돈 작업을 수행한다.

초기 MVP에서는 복잡한 VLA/VLM 기반 판단을 바로 적용하지 않고, **rule-based FSM**으로 전체 작업 흐름을 먼저 구현한다. 이후 데이터가 쌓이면 FSM 전체를 제거하는 것이 아니라, FSM 내부의 `PLAN` 단계만 VLM/VLA 기반 Planner로 교체한다.

핵심 원칙은 다음과 같다.

> FSM은 끝까지 유지하고, Planner만 교체 가능하게 만든다.

---

## 2. 전체 구조 요약

Cleany의 작업 흐름은 다음 3계층으로 나눈다.

```text
Perception Layer
    ↓
Planning Layer
    ↓
Execution Layer
```

### 2.1 Perception Layer

카메라, RGB-D, LiDAR, IMU 등 센서 입력을 기반으로 현재 환경 상태를 인식한다.

주요 역할:

- 책상, 바닥, 의자 주변의 객체 후보 탐지
- 쓰레기 / 분실물 후보 / 기타 물체 / unknown 분류
- bbox, confidence, depth, 3D pose 후보 생성
- 작업 가능한 물체인지 판단하기 위한 기초 정보 제공

예시 출력:

```json
{
  "objects": [
    {
      "object_id": "obj_001",
      "class_name": "trash",
      "confidence": 0.86,
      "bbox": [120, 80, 260, 220],
      "pose_frame": "camera_color_optical_frame",
      "action_hint": "pick"
    }
  ]
}
```

### 2.2 Planning Layer

Perception 결과와 로봇 상태를 바탕으로 다음 작업을 결정한다.

초기 MVP에서는 `RuleBasedPlanner`가 if-else 기반으로 task를 생성한다.  
고도화 단계에서는 `VLMPlanner`가 이미지, 객체 리스트, 현재 상태를 입력받아 skill sequence를 생성한다.

중요한 점은 Mission Manager가 특정 Planner 구현에 의존하지 않아야 한다는 것이다.

```text
Mission Manager
    └── Planner Interface
            ├── RuleBasedPlanner
            └── VLMPlanner
```

### 2.3 Execution Layer

Planning Layer에서 생성한 skill sequence를 실제 로봇 동작으로 변환한다.

주요 역할:

- Nav2 기반 이동
- MoveIt / LeRobot / XLeRobot 기반 팔 제어
- gripper 제어
- skill 성공/실패 반환
- timeout, retry, fail-safe 처리

---

## 3. FSM 상태 정의

초기 Mission Manager는 다음 FSM을 기준으로 구현한다.

```text
IDLE
  → SCAN
  → DETECT_OBJECTS
  → PLAN
  → EXECUTE_SKILL
  → VERIFY
  → REPORT
  → IDLE
```

### 3.1 IDLE

로봇이 대기 중인 상태.

진입 조건:

- 시스템 시작 직후
- 이전 mission 완료
- 사용자가 stop/reset 요청
- error 복구 완료

주요 동작:

- 로봇 상태 확인
- battery, sensor, actuator health check
- mission start 요청 대기

전이 조건:

- mission start 수신 → `SCAN`
- hardware error 감지 → `ERROR`

---

### 3.2 SCAN

작업 공간을 스캔하는 상태.

주요 동작:

- 카메라 프레임 수집
- depth frame 수집
- 필요 시 로봇 head/camera pose 변경
- perception trigger 호출

전이 조건:

- 이미지 수집 성공 → `DETECT_OBJECTS`
- 센서 입력 실패 → `ERROR`
- timeout → `REPORT` 또는 `ERROR`

---

### 3.3 DETECT_OBJECTS

Perception Layer가 객체 후보를 탐지하는 상태.

주요 동작:

- object detection / segmentation 수행
- 쓰레기, 분실물 후보, 기타 물체 분류
- bbox, confidence, pose 후보 생성
- world_state 갱신

전이 조건:

- 객체 후보 있음 → `PLAN`
- 객체 후보 없음 → `REPORT`
- confidence가 전반적으로 낮음 → `SCAN`
- perception error → `ERROR`

---

### 3.4 PLAN

탐지 결과와 현재 로봇 상태를 바탕으로 다음 skill sequence를 생성하는 상태.

초기 구현:

- `RuleBasedPlanner` 사용

고도화 구현:

- `VLMPlanner` 또는 `VLAPlanner` 사용

입력:

- world_state
- detected_objects
- robot_state
- failure_history
- mission_config

출력:

- task
- skill_sequence

예시 rule:

```text
trash detected      → collect_trash
lost_item detected  → store_lost_item
unknown detected    → skip or ask_human
low confidence      → rescan
workspace outside   → skip
```

전이 조건:

- 유효한 skill sequence 생성 → `EXECUTE_SKILL`
- 실행 가능한 작업 없음 → `REPORT`
- planner error → `ERROR`

---

### 3.5 EXECUTE_SKILL

선택된 skill을 실행하는 상태.

예시 skill:

- `navigate_to`
- `pick_object`
- `place_object`
- `push_object`
- `inspect_area`
- `return_to_home`

주요 동작:

- Skill Executor 호출
- action result 대기
- timeout 관리
- 실패 시 retry 여부 판단

전이 조건:

- skill 성공 → 다음 skill 또는 `VERIFY`
- skill 실패 후 retry 가능 → `EXECUTE_SKILL`
- skill 실패 후 retry 불가 → `REPORT`
- hardware error → `ERROR`

---

### 3.6 VERIFY

작업 성공 여부를 검증하는 상태.

주요 동작:

- 작업 후 재촬영
- 대상 객체가 사라졌는지 확인
- 쓰레기통 / 보관함에 물체가 들어갔는지 확인
- 전후 상태 비교

전이 조건:

- 성공 검증 → `REPORT`
- 실패 검증 → retry 가능 시 `PLAN` 또는 `EXECUTE_SKILL`
- 검증 불가 → `REPORT`

---

### 3.7 REPORT

작업 결과를 로그와 대시보드에 기록하는 상태.

주요 동작:

- 작업 성공/실패 로그 저장
- 실패 원인 기록
- 이미지 snapshot 저장
- dashboard event publish
- 필요 시 서버 업로드

전이 조건:

- mission 종료 → `IDLE`
- 추가 작업 존재 → `PLAN`

---

### 3.8 ERROR

시스템 오류 상태.

주요 동작:

- 로봇 정지
- 현재 task 중단
- error_code 기록
- dashboard에 error publish
- 사용자 개입 필요 여부 판단

전이 조건:

- reset 요청 → `IDLE`
- 자동 복구 가능 → 이전 안정 상태
- 복구 불가 → `ERROR` 유지

---

## 4. Planner 교체 구조

Planner는 Mission Manager 내부에서 호출되는 독립 모듈로 둔다.

Mission Manager는 Planner가 rule-based인지 VLM-based인지 알 필요가 없다.  
Planner는 동일한 입력과 출력을 가져야 한다.

### 4.1 Planner Interface

```python
class Planner:
    def plan(self, world_state, robot_state, mission_config):
        raise NotImplementedError
```

### 4.2 RuleBasedPlanner

초기 MVP용 Planner.

장점:

- 예측 가능함
- 디버깅 쉬움
- 안전 조건을 명확히 넣기 쉬움
- 로봇 도착 전에도 mock으로 검증 가능

예시:

```python
class RuleBasedPlanner(Planner):
    def plan(self, world_state, robot_state, mission_config):
        objects = world_state.objects

        trash_candidates = [
            obj for obj in objects
            if obj.class_name == "trash"
            and obj.confidence >= mission_config.min_confidence
            and obj.is_reachable
        ]

        if trash_candidates:
            target = max(trash_candidates, key=lambda x: x.confidence)
            return SkillSequence([
                SkillCommand("pick_object", target_object_id=target.object_id),
                SkillCommand("place_object", target_location="trash_bin")
            ])

        return SkillSequence([])
```

### 4.3 VLMPlanner

고도화 단계용 Planner.

VLMPlanner는 이미지, 객체 리스트, 환경 상태, 실패 이력 등을 입력으로 받아 skill sequence를 생성한다.

VLM이 직접 모터나 관절을 제어하지 않는다.  
VLM은 어떤 skill을 어떤 순서로 호출할지 결정한다.

예시 출력:

```json
{
  "task": "collect_trash",
  "target_object_id": "obj_003",
  "skill_sequence": [
    {
      "skill": "pick_object",
      "args": {
        "object_id": "obj_003"
      }
    },
    {
      "skill": "place_object",
      "args": {
        "target_location": "trash_bin"
      }
    }
  ],
  "reason": "The object appears to be a disposable paper cup."
}
```

---

## 5. Safety Guard

VLMPlanner를 사용하더라도 최종 실행 전에는 반드시 rule-based safety guard를 통과해야 한다.

VLM의 판단은 참고할 수 있지만, 실행 권한을 그대로 넘겨서는 안 된다.

### 5.1 실행 전 검사

각 skill 실행 전 다음 조건을 확인한다.

- confidence가 기준 이상인가?
- depth 값이 유효한가?
- target pose가 로봇팔 workspace 안에 있는가?
- target이 노트북, 휴대폰, 지갑 등 개인 소지품일 가능성이 높은가?
- 충돌 위험이 없는가?
- 같은 작업을 너무 많이 실패하지 않았는가?
- emergency stop 상태가 아닌가?
- 배터리와 전원 상태가 충분한가?

### 5.2 실패 원인 코드

실패 원인은 반드시 구조화해서 남긴다.

```text
DETECTION_FAIL
DEPTH_FAIL
LOW_CONFIDENCE
OUT_OF_WORKSPACE
GRASP_FAIL
PLACE_FAIL
NAVIGATION_FAIL
COLLISION_RISK
HARDWARE_ERROR
TIMEOUT
UNKNOWN_OBJECT
USER_INTERVENTION_REQUIRED
```

이 실패 원인은 나중에 다음 용도로 사용한다.

- 대시보드 표시
- 실험 결과 분석
- VLA/IL 학습 데이터 정제
- Sim-to-Real 실패 케이스 재현
- 발표/보고서의 정량 지표

---

## 6. ROS2 인터페이스 초안

팀 논의 전까지는 아래를 초안으로 둔다.

### 6.1 주요 노드

```text
cleany_vision_node
cleany_mission_manager
cleany_planner
cleany_skill_executor
cleany_robot_interface
cleany_dashboard_bridge
cleany_logger
```

### 6.2 주요 토픽

```text
/cleany/perception/objects
/cleany/mission/state
/cleany/mission/current_task
/cleany/robot/state
/cleany/log/event
```

### 6.3 주요 액션

```text
/cleany/skills/navigate_to
/cleany/skills/pick_object
/cleany/skills/place_object
/cleany/skills/push_object
```

### 6.4 주요 서비스

```text
/cleany/mission/start
/cleany/mission/stop
/cleany/mission/reset
/cleany/perception/trigger_scan
/cleany/report/generate
```

---

## 7. Mock → Sim → Real 교체 전략

초기 개발은 실제 로봇 없이 진행한다.

### 7.1 Mock 단계

목표:

- Mission Manager 상태 흐름 검증
- Planner 입출력 검증
- dashboard/logging 검증
- skill success/fail 처리 검증

구현:

```text
MockVisionNode
    → MissionManager
        → RuleBasedPlanner
            → MockRobotInterface
                → Logger / Dashboard
```

### 7.2 Sim 단계

목표:

- Isaac Sim 또는 MuJoCo에서 특정 skill 검증
- 파지, 접근, 정돈 동작의 반복 실험
- 실패 케이스 재현
- real robot 도입 전 시나리오 테스트

주의:

- 시뮬레이션은 실제 로봇 모델과 센서 위치가 어느 정도 확정된 뒤 본격화한다.
- 초기부터 Isaac Sim을 메인 병목으로 만들지 않는다.

### 7.3 Real 단계

목표:

- XLeRobot 실제 하드웨어와 연결
- 카메라/RGB-D/LiDAR/IMU 토픽 확인
- robot interface를 실제 driver로 교체
- pick-and-place 또는 waypoint 이동 MVP 통합

구현:

```text
RealVisionNode
    → MissionManager
        → RuleBasedPlanner or VLMPlanner
            → XLeRobotInterface
                → Logger / Dashboard
```

---

## 8. 초기 MVP 정의

초기 MVP는 다음 범위로 제한한다.

> 고정된 위치의 카메라 이미지에서 쓰레기 후보를 인식하고, Mission Manager가 수거 task를 생성하며, Mock 또는 실제 Robot Interface가 pick-and-place skill을 수행하고, 결과 로그가 남는 end-to-end 파이프라인.

### 포함

- 이미지 입력
- 객체 후보 탐지
- rule-based task 생성
- mock skill execution
- success/failure result
- event logging
- 간단한 dashboard 또는 CLI 출력

### 제외 또는 후순위

- 완전 자율주행
- 복잡한 VLA 파인튜닝
- 강화학습 기반 파지 정책
- 의자 정리
- 테이블 닦기
- 소등/문단속
- 멀티룸 map 관리
- 상용 수준 대시보드

---

## 9. 개발 우선순위

### Phase 0: 로봇 도착 전

- Mission Manager FSM 구현
- RuleBasedPlanner 구현
- MockVisionNode 구현
- MockRobotInterface 구현
- 실패 원인 코드 정의
- ROS2 message/action/service 초안 작성
- 책상 환경 이미지 데이터 수집
- bringup checklist 작성

### Phase 1: 로봇 도착 직후

- 부품 검수
- 전원 테스트
- 서보/모터 개별 테스트
- 카메라/RGB-D/LiDAR/IMU 인식 확인
- ROS2 topic 확인
- TF tree 초안 구성
- 실제 RobotInterface 작성

### Phase 2: 1차 통합

- 고정 위치 pick-and-place
- 객체 인식 결과와 target pose 연결
- 수거함 위치 고정
- task success/failure logging
- 시연 가능한 단일 시나리오 완성

### Phase 3: 고도화

- Nav2 이동 추가
- VLMPlanner 도입
- Isaac Sim 기반 skill 검증
- 실패 케이스 재학습 루프
- dashboard 고도화

---

## 10. 설계 원칙

1. FSM은 상태 관리와 안전 제어를 담당한다.
2. VLM/VLA는 고수준 작업 계획에만 사용한다.
3. 실제 로봇 제어는 Skill Executor와 ROS2 제어 계층이 담당한다.
4. Planner는 rule-based에서 VLM-based로 교체 가능해야 한다.
5. 실패 원인은 반드시 구조화해서 남긴다.
6. Mock, Sim, Real은 같은 interface를 사용해야 한다.
7. 초기 MVP에서는 완성도 높은 단일 시나리오를 우선한다.
8. 중간발표 전에는 “많은 기능”보다 “확실히 되는 기능”이 중요하다.

---

## 11. 팀 회의에서 결정해야 할 것

다음 항목은 팀원과 합의가 필요하다.

- 최종 ROS2 패키지 구조
- custom msg/action/service 형식
- 좌표계 frame 이름
- 초기 MVP 시나리오
- 로봇 도착 후 bringup 담당자
- Raspberry Pi 사용 여부
- Jetson 단독 구조 여부
- Isaac Sim 우선순위
- Vision 모델 후보
- 수거 대상 class 정의
- 분실물/소지품 처리 정책
- dashboard 최소 기능

---

## 12. 한 줄 요약

초기에는 rule-based FSM으로 Cleany의 전체 작업 파이프라인을 뚫고, 이후 FSM의 `PLAN` 단계만 VLM/VLA 기반 Planner로 교체한다. FSM은 안전, 상태 관리, 재시도, 실패 로그를 위해 끝까지 유지한다.
