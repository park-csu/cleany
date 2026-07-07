from __future__ import annotations

from pathlib import Path
from typing import Any

import mujoco
from ament_index_python.packages import get_package_share_directory


def default_scene_path() -> Path:
    share_dir = Path(get_package_share_directory('cleany_mujoco_sim'))
    return share_dir / 'hardware' / 'scene.xml'


def load_model(scene_path: Path) -> tuple[Any, Any]:
    model = mujoco.MjModel.from_xml_path(str(scene_path))
    data = mujoco.MjData(model)
    return model, data
