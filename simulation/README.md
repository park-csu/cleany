# 시뮬레이션

이 디렉터리는 Cleany의 시뮬레이션 환경을 관리합니다.

## MuJoCo

MuJoCo 시뮬레이션은 [`mujoco/`](./mujoco/) 디렉터리에 있습니다.

```bash
cd simulation/mujoco
uv sync
uv run python main.py
```

각 시뮬레이터는 필요에 따라 독립적인 의존성과 도구 설정을 가질 수 있습니다.
