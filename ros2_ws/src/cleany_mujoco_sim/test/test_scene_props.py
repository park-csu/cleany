"""Integration smoke test for the real installed scene.

Unlike ``test_scene_loader.py`` (which loads a tiny synthetic MJCF), this test
compiles the actual ``hardware/scene.xml`` from the installed package share
directory, so it exercises the ``props.xml`` include, the mug meshes/texture,
and the ``assetdir`` asset-path resolution end to end.
"""

from __future__ import annotations

import mujoco
import pytest

from cleany_mujoco_sim.scene_loader import default_scene_path, load_model

# Bodies introduced by props.xml (table + three grasp targets).
PROP_BODIES = ["table", "can1", "box1", "mug1"]


@pytest.fixture
def real_scene_path():
    path = default_scene_path()
    if not path.exists():
        pytest.skip(f"installed scene not found at {path}; build the package first")
    return path


def test_real_scene_compiles_and_steps(real_scene_path):
    model, data = load_model(real_scene_path)
    mujoco.mj_step(model, data)
    assert data.time > 0.0


def test_real_scene_includes_prop_bodies(real_scene_path):
    model, _ = load_model(real_scene_path)
    for name in PROP_BODIES:
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
        assert body_id != -1, f"prop body '{name}' missing from compiled scene"


def test_real_scene_grasp_targets_are_dynamic(real_scene_path):
    """can1/box1/mug1 use a freejoint so they fall onto the table under gravity."""
    model, _ = load_model(real_scene_path)
    for name in ["can1", "box1", "mug1"]:
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
        assert model.body_dofnum[body_id] == 6, f"'{name}' is not a free body"
