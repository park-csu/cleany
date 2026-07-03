# Cleany — AI 에이전트는 움직이고 싶어

## 프로젝트 개요

**끌리니(Cleany) - 무인 공간 관리 로봇**  
무인 스터디카페·독서실·공유오피스 등 공간 대여 점포에서 퇴실 후 정리 업무(쓰레기 수거, 분실물 보관, 집기 정리, 테이블 닦기, 소등/문단속)를 자동화하는 이동형 로봇.

- **팀명**: AI 에이전트는 움직이고 싶어
- **팀원**: 이동근 (PM/SLAM/백엔드), 박창수 (HW/시스템통합), 이정현 (Vision/VLA)
- **프로그램**: AI·SW마에스트로 제17기
- **키워드**: Physical AI · Robotics · Vision-Language-Action · Sim-to-Real

## 지식 베이스 (Knowledge Base)

이 프로젝트의 모든 정리된 지식은 `gdrive/Obsidian_Vault/`에 있다.  
**모르는 것이 있으면 아래 파일을 순서대로 읽어라.**

```
gdrive/Obsidian_Vault/
├── llms.txt                        ← LLM 진입점 (가장 먼저)
├── 00_Index/
│   ├── Home.md                     ← 전체 구조 요약
│   ├── Project-Overview.md         ← 프로젝트 개요
│   ├── Current-Status.md           ← 현재 상태 / 블로커
│   ├── Roadmap.md                  ← 로드맵 & 서브시스템
│   └── Glossary.md                 ← 용어 정의
├── 01_Agent-Memory/
│   ├── Agent-Instructions.md       ← 에이전트 동작 규칙
│   ├── Project-Context.md          ← 프로젝트 컨텍스트
│   ├── Team-Context.md             ← 팀 컨텍스트
│   ├── Current-Priorities.md       ← 현재 우선순위
│   └── Known-Issues.md             ← 알려진 문제
├── 02_Operations/
│   ├── Workflow.md                 ← 작업 흐름 & DoD
│   └── Discord-Automation-Routing.md
├── 03_Decisions/
│   └── Important-Decisions.md      ← ADR 및 중요 결정
└── raw/google-drive/               ← Google Drive 원본 파일 (읽기 전용)
```

주제별 상세 정보:
- 기획서 원문: `gdrive/Obsidian_Vault/raw/google-drive/[기획서]-AI-에이전트는-움직이고-싶어.md`
- 시스템 아키텍처/FSM: `ros2_ws/src/cleany_mission_manager/DESIGN.md`
- 개발 로드맵: `gdrive/Obsidian_Vault/development-roadmap.md`
- 협업 구조: `gdrive/Obsidian_Vault/collaboration-structure.md`

### Google Drive 접근 메모

- `gdrive/`는 `rclone mount` 기반 FUSE 경로다. `Input/output error`가 나면 Google Drive 원격 자체보다 FUSE 마운트 또는 토큰 상태가 깨졌을 가능성을 먼저 의심한다.
- 원격 직접 조회는 `rclone lsd gdrive:`로 확인한다. 이 명령이 되는데 `gdrive/...` 경로만 안 되면 마운트 문제다.
- LLMWiki 전체 파일 목록 조회, 백업, 동기화처럼 재귀적으로 많은 파일을 훑을 때는 `--fast-list`를 사용한다. 예: `rclone lsf gdrive:Obsidian_Vault --recursive --fast-list`
- `--fast-list`는 API 호출 수를 줄이는 대신 메모리를 더 쓴다. 단일 파일 읽기나 얕은 목록 조회에는 큰 의미가 없고, FUSE 마운트 오류를 직접 고치는 옵션도 아니다.

## Source of Truth

| 정보 종류 | 기준 저장소 |
|---|---|
| 작업 상태 | Jira |
| 코드 변경 | GitHub PR |
| 원본 파일 | Google Drive (`gdrive/`) |
| 정리된 지식 | LLMWiki (`gdrive/Obsidian_Vault/`) |
| 빠른 논의 | Discord |
| 기술/디자인 결정 | ADR + `Important-Decisions.md` |

## 시스템 아키텍처

### 3계층 구조

```
Perception Layer   → 객체 탐지 (카메라/RGB-D/LiDAR)
Planning Layer     → 작업 계획 (RuleBasedPlanner → VLMPlanner)
Execution Layer    → 로봇 제어 (Nav2/MoveIt/LeRobot)
```

### FSM 상태

```
IDLE → SCAN → DETECT_OBJECTS → PLAN → EXECUTE_SKILL → VERIFY → REPORT → IDLE
                                                                  ↓
                                                               ERROR
```

### ROS2 핵심 노드

```
cleany_vision_node          # 인식
cleany_mission_manager      # FSM / 상태 관리
cleany_planner              # RuleBasedPlanner | VLMPlanner
cleany_skill_executor       # navigate_to, pick_object, place_object, push_object
cleany_robot_interface      # Mock → Sim → Real 교체 지점
cleany_dashboard_bridge     # 대시보드 이벤트
cleany_logger               # 실패 원인 코드 포함 로그
```

### 핵심 ROS2 인터페이스

| 종류 | 이름 |
|---|---|
| Topic | `/cleany/perception/objects`, `/cleany/mission/state`, `/cleany/log/event` |
| Action | `/cleany/skills/navigate_to`, `/cleany/skills/pick_object`, `/cleany/skills/place_object` |
| Service | `/cleany/mission/start`, `/cleany/mission/stop`, `/cleany/mission/reset` |

## 기술 스택

| 구분 | 항목 |
|---|---|
| OS | Ubuntu 26.04 LTS (JetPack 7.2) |
| 로봇 | XLeRobot (모바일 매니퓰레이터) |
| 컴퓨팅 | NVIDIA Jetson AGX Orin 64GB |
| 미들웨어 | ROS 2 |
| 시뮬레이션 | Isaac Sim, MuJoCo |
| 언어 | C++ (ROS 2), Python (PyTorch, OpenCV, TensorRT) |
| 센서 | Camera/RGB-D, 2D LiDAR, IMU |
| AI 추론 | 경량 Object Detection, 경량 VLM, Agentic VLA |
| 학습 | LeRobot, Isaac Sim 기반 Sim-to-Real |

## 서브시스템

- **EDG** — 로봇 엣지 시스템 (Vision, Mission Manager, Skill Executor)
- **HW** — 하드웨어 플랫폼 (XLeRobot 조립, Jetson 셋업, 센서)
- **SIM** — 시뮬레이션·학습 (Isaac Sim, MuJoCo, RL/IL)
- **BE** — 백엔드 서버
- **FE** — 관리자 대시보드
- **INF** — 공통·인프라

## 워크플로우

```
아이디어/버그 → Discord/Jira 논의
→ Jira Issue 생성
→ GitHub Branch 생성
→ 개발/실험/문서 작업
→ PR 리뷰 & merge
→ 시뮬레이션/하드웨어 검증
→ Drive 결과 저장
→ LLMWiki 요약 기록
→ Jira Done
→ Sprint KPT
```

**Definition of Done**: Jira 요구사항 충족 + 본인 테스트 + PR merge + 시뮬/HW 검증 + Drive 저장 + (필요 시) LLMWiki 문서화 + (필요 시) ADR 작성

## 개발 단계 (Mock → Sim → Real)

- **Phase 0** (로봇 도착 전): Mission Manager FSM, RuleBasedPlanner, MockVisionNode, MockRobotInterface
- **Phase 1** (로봇 도착 직후): 부품 검수, 센서 확인, ROS2 토픽 확인
- **Phase 2** (1차 통합): 고정 위치 pick-and-place, 수거함 연결, 단일 시나리오 시연
- **Phase 3** (고도화): Nav2 자율주행, VLMPlanner, Isaac Sim 검증, 대시보드

## 설계 원칙

1. FSM은 상태 관리와 안전 제어를 담당한다 — 끝까지 유지한다.
2. VLM/VLA는 고수준 작업 계획(`PLAN` 단계)에만 사용한다.
3. Planner는 RuleBasedPlanner → VLMPlanner로 교체 가능해야 한다.
4. Mock, Sim, Real은 동일한 인터페이스를 사용해야 한다.
5. 실패 원인은 반드시 구조화해서 남긴다 (`GRASP_FAIL`, `LOW_CONFIDENCE` 등).
6. 초기 MVP에서는 "많은 기능"보다 "확실히 되는 기능"을 우선한다.

## 운영 규칙

- Agent 생성 결과물은 초안(draft)으로 표시한다.
- 코드·문서·결정 초안은 반드시 원본 파일 경로 또는 출처 링크를 포함한다.
- 중요한 결정은 사람이 최종 확인한다. 팀원 승인 없이 확정으로 처리하지 않는다.
- Discord에서 결정된 중요한 내용은 반드시 Jira, LLMWiki, ADR 중 하나로 옮긴다.
- 실험 기록은 성공/실패와 무관하게 남긴다.
- `raw/` 하위 파일은 읽기 전용이다. 직접 수정하지 않는다.

## Discord 라우팅

| 채널 | 용도 |
|---|---|
| `#agent-control` | 작업 지시, 대화, Agent 제어 |
| `<#1519573134712373370>` | 모든 Automation 처리 보고 |

Automation report channel ID: `1519573134712373370`

## LLMWiki 업데이트 기준

새 지식이 생겼을 때 업데이트할 파일:
- 진행 상태 변경 → `00_Index/Current-Status.md`
- 기술/디자인 결정 → `03_Decisions/Important-Decisions.md`
- 팀 운영 방식 변경 → `02_Operations/Workflow.md`
- 실험 결과 → `03_Decisions/` 또는 별도 실험 기록 파일
- 새 용어 → `00_Index/Glossary.md`
- 인덱스 변경 시 → `gdrive/Obsidian_Vault/index.md`, `log.md` 함께 업데이트

## 코드 작업 시 주의사항

- ROS2 노드·토픽·서비스 이름은 위 인터페이스 표 기준을 따른다.
- Planner 구현은 반드시 `Planner` 인터페이스(`plan(world_state, robot_state, mission_config)`)를 상속한다.
- Mock/Sim/Real은 동일한 `robot_interface`를 사용해야 한다 — 분기 처리 금지.
- Safety Guard를 우회하는 코드를 작성하지 않는다.
- 실패 원인은 아래 코드 중 하나로 반환한다:
  `DETECTION_FAIL`, `DEPTH_FAIL`, `LOW_CONFIDENCE`, `OUT_OF_WORKSPACE`,
  `GRASP_FAIL`, `PLACE_FAIL`, `NAVIGATION_FAIL`, `COLLISION_RISK`,
  `HARDWARE_ERROR`, `TIMEOUT`, `UNKNOWN_OBJECT`, `USER_INTERVENTION_REQUIRED`
