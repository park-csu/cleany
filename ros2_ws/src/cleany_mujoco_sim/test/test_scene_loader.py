from pathlib import Path

import mujoco

from cleany_mujoco_sim.scene_loader import load_model


def test_load_model_from_xml_path(scene_path: Path):
    model, data = load_model(scene_path)

    assert model.njnt == 2
    mujoco.mj_step(model, data)
    assert data.time > 0.0
