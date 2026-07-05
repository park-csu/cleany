from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

import mujoco
import mujoco.viewer

DEFAULT_SCENE = Path(__file__).parent / "hardware" / "scene.xml"


def load_model(scene_path: Path) -> tuple[Any, Any]:
    """Load a MuJoCo XML scene and create its runtime data."""
    model = mujoco.MjModel.from_xml_path(str(scene_path))
    data = mujoco.MjData(model)
    return model, data


def run_viewer(scene_path: Path) -> None:
    """Open a simple MuJoCo viewer and step the loaded scene in real time."""
    model, data = load_model(scene_path)

    print(f"Loaded MuJoCo scene: {scene_path}")
    print(
        "Model summary: "
        f"nq={model.nq}, nv={model.nv}, nu={model.nu}, "
        f"nbody={model.nbody}, njnt={model.njnt}"
    )

    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            step_started = time.time()

            mujoco.mj_step(model, data)
            viewer.sync()

            sleep_time = model.opt.timestep - (time.time() - step_started)
            if sleep_time > 0:
                time.sleep(sleep_time)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load hardware/scene.xml in MuJoCo viewer.")
    parser.add_argument(
        "scene",
        nargs="?",
        type=Path,
        default=DEFAULT_SCENE,
        help=f"Path to a MuJoCo scene XML. Defaults to {DEFAULT_SCENE}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scene_path = args.scene.expanduser().resolve()
    if not scene_path.exists():
        raise FileNotFoundError(f"MuJoCo scene XML not found: {scene_path}")

    run_viewer(scene_path)


if __name__ == "__main__":
    main()
