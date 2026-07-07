import pytest
from rclpy.time import Time
from sensor_msgs.msg import JointState

from cleany_mujoco_sim.state import (
    actuated_joint_names,
    apply_joint_cmd,
    joint_positions,
    joint_state_msg,
    steps_per_tick,
)


def test_actuated_joint_names_skips_freejoint(model_data):
    model, _ = model_data
    assert actuated_joint_names(model) == ["shoulder"]


def test_joint_positions_matches_qpos(model_data):
    model, data = model_data
    data.qpos[model.jnt_qposadr[1]] = 0.5
    assert joint_positions(model, data) == pytest.approx([0.5])


def test_joint_state_msg_fields(model_data):
    model, data = model_data
    msg = joint_state_msg(model, data, Time())
    assert msg.name == ["shoulder"]
    assert msg.position == pytest.approx(joint_positions(model, data))


def test_apply_joint_cmd_writes_qpos(model_data):
    model, data = model_data
    cmd = JointState()
    cmd.name = ["shoulder"]
    cmd.position = [0.3]
    apply_joint_cmd(model, data, cmd)
    assert data.qpos[model.jnt_qposadr[1]] == pytest.approx(0.3)


def test_steps_per_tick_matches_tick_period_to_timestep():
    assert steps_per_tick(timestep=0.002, publish_rate_hz=60.0) == 8


def test_steps_per_tick_never_zero_when_timestep_exceeds_tick_period():
    assert steps_per_tick(timestep=0.1, publish_rate_hz=60.0) == 1
