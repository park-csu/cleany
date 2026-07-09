# AGENTS.md

이 문서는 Cleany 구현 레포에서 AI 코딩 에이전트가 따라야 할 작업 규칙이다. 제품/기획 근거는 `docs/cleany-docs/` submodule의 KB를 우선 참고한다.

## 1. 저장소 성격

- 이 저장소는 끌리니(Cleany) 로봇 엣지 시스템 구현 레포다.
- 핵심 구현은 `ros2_ws/`의 ROS 2 workspace에 둔다.
- `docs/cleany-docs/`는 기획/예비설계 KB submodule이다. 비어 있거나 누락되었으면 먼저 실행한다.

```bash
git submodule update --init --recursive docs/cleany-docs
```

- `docs/cleany-docs/`를 수정해야 하는 명시 요청이 있을 때만 submodule 내부 파일을 편집한다. 그때는 `docs/cleany-docs/AGENTS.md`를 따른다.
- `ros2_ws/build/`, `ros2_ws/install/`, `ros2_ws/log/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/` 같은 생성물은 편집하지 않는다.

## 2. 작업 전 기준 문서

제품 범위나 아키텍처에 영향을 주는 작업 전에는 필요한 문서를 먼저 확인한다.

- 현재 상태: `docs/cleany-docs/00_START_HERE/02 - Current Status.md`
- 미해결 질문: `docs/cleany-docs/10_PLANNING/08 - Questions.md`
- 기술 개요: `docs/cleany-docs/20_TECHNICAL/00 - Technical Overview.md`
- 시스템 개념: `docs/cleany-docs/20_TECHNICAL/01 - System Concept.md`
- Rule-based VLA: `docs/cleany-docs/20_TECHNICAL/03 - Rule-based VLA Architecture.md`
- 안전/리스크: `docs/cleany-docs/20_TECHNICAL/08 - Safety and Risk.md`
- 구현 상세는 각 패키지 README도 함께 확인한다.

KB 문서 대부분은 `draft`, `needs-human-review` 상태다. 확정되지 않은 내용(MVP 범위, 대시보드 포함 여부, 안전 기준, Jetson/ROS/JetPack 조합, XLeRobot 세부 사양 등)을 코드에서 단정하거나 하드코딩하지 않는다.

## 3. 아키텍처 원칙

- 초기 MVP 흐름은 `IDLE → NAVIGATE_TO_TARGET → PERCEIVE → PLAN_TASKS → EXECUTE_TASKS → RETURN_HOME → REPORT`를 기준으로 한다.
- Mission Manager만 FSM 상태 전이 권한을 가진다. Navigator, Perception, Planner, Skill Executor는 상태를 직접 바꾸지 않고 `ModuleResult`를 반환한다.
- Perception은 객체/공간 상태를 제공하고 최종 행동 결정을 하지 않는다.
- Planner는 `collect`, `skip`, `store_lost_item`, `human_review` 같은 high-level task와 skill sequence를 만든다. grasp pose, IK, trajectory, gripper 제어는 Planner 책임이 아니다.
- Skill Executor는 high-level skill을 실행 가능한 세부 동작으로 분해하고 Robot Interface/Nav2/MoveIt/LeRobot 등에 위임한다.
- 불확실한 물체, 낮은 confidence, 안전 리스크는 보수적으로 `skip`, `human_review`, `BLOCKED`, `FAILED`로 처리한다. 분실물을 쓰레기로 단정하지 않는다.
- Mock/Sim/Real 구현은 인터페이스 뒤에 분리한다. 실제 하드웨어, 센서, 좌표계, 안전 한계는 `configs/` 또는 명시적 adapter에 둔다.

## 4. 코드 작성 규칙

- Python 코드는 type hint, 작은 dataclass/model, 명확한 port/interface를 선호한다.
- ROS 2 node와 순수 core logic을 가능하면 분리해 core logic은 pytest로 빠르게 검증 가능하게 한다.
- 패키지 경계를 넘는 의존은 명시적 interface/message/config를 통해 연결한다.
- 설정값은 코드에 숨겨 하드코딩하지 말고 `configs/mission/`, `configs/robot/` 또는 ROS parameter로 이동할 수 있게 작성한다.
- ROS 패키지 dependency를 추가하면 `package.xml`, `setup.py`/`setup.cfg`, 필요 시 `ros2_ws/rosdep/cleany.yaml`을 함께 갱신한다.
- 생성 파일, 대용량 asset, mesh 파일은 명시 요청 없이 재생성하거나 포맷하지 않는다.

## 5. 자주 쓰는 명령

Docker 기반 ROS 2 Humble 개발 환경을 기본으로 사용한다.

```bash
./scripts/docker-build-humble.sh
./scripts/docker-up-humble.sh
./scripts/rosdep install --from-paths ros2_ws/src --ignore-src -r -y
./scripts/ros2-build
./scripts/ros2-test
```

타깃 pytest 예시:

```bash
./scripts/pytest-ros src/cleany_mission_manager/tests/test_mission_flow.py
./scripts/pytest-ros src/cleany_mujoco_sim/test/test_scene_loader.py
```

ROS 실행 예시:

```bash
./scripts/ros2 launch cleany_mujoco_sim mujoco_sim.launch.py headless:=true
```

## 6. 검증 규칙

- 코드를 바꿨으면 가장 작은 관련 테스트를 먼저 실행한다.
- FSM/core logic 변경: 해당 패키지 pytest를 우선 실행한다.
- ROS package manifest, launch, install data 변경: `./scripts/ros2-build` 또는 관련 패키지 build를 실행한다.
- 여러 패키지 경계나 ROS interface를 바꿨으면 `./scripts/ros2-test`까지 고려한다.
- 검증을 실행하지 못했으면 최종 응답에 이유와 대신 확인한 내용을 적는다.

## 7. 문서/결정 처리

- 구현 중 KB와 충돌하거나 추가 결정이 필요한 사항을 발견하면 임의로 확정하지 않는다.
- 코드에는 최소한의 TODO/주석으로 불확실성을 남기고, 필요하면 `docs/cleany-docs/10_PLANNING/08 - Questions.md` 또는 Decision 후보 갱신을 사용자에게 제안한다.
- `status: selected`, `review_status: reviewed` 같은 확정 상태는 사람 검토 없이 만들거나 변경하지 않는다.
