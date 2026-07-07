import time
from pathlib import Path

import pytest
import rclpy
from rclpy.parameter import Parameter
from sensor_msgs.msg import JointState

from cleany_mujoco_sim.sim_node import MujocoSimNode
from cleany_mujoco_sim.state import joint_positions


def _make_node(scene_path: Path, **overrides) -> MujocoSimNode:
    params = {
        'scene_path': str(scene_path),
        'publish_rate_hz': 1000.0,
        'headless': True,
    }
    params.update(overrides)
    return MujocoSimNode(
        parameter_overrides=[Parameter(name, value=value) for name, value in params.items()]
    )


def test_sim_node_publishes_joint_states(scene_path: Path):
    rclpy.init(args=[])
    try:
        node = _make_node(scene_path)
        received: list[JointState] = []
        node.create_subscription(JointState, 'joint_states', received.append, 10)

        deadline = time.time() + 2.0
        while not received and time.time() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)

        assert received
        assert received[0].name == ['shoulder']
    finally:
        node.destroy_node()
        rclpy.shutdown()


def test_sim_node_applies_joint_cmd(scene_path: Path):
    rclpy.init(args=[])
    try:
        node = _make_node(scene_path)
        commander = rclpy.create_node('test_commander')
        cmd_pub = commander.create_publisher(JointState, '/mujoco_sim/joint_cmd', 10)

        cmd = JointState()
        cmd.name = ['shoulder']
        cmd.position = [0.4]

        applied = False
        deadline = time.time() + 2.0
        while time.time() < deadline:
            cmd_pub.publish(cmd)
            rclpy.spin_once(node, timeout_sec=0.05)
            if joint_positions(node._model, node._data) == pytest.approx([0.4]):
                applied = True
                break

        assert applied
        commander.destroy_node()
    finally:
        node.destroy_node()
        rclpy.shutdown()


def test_sim_node_rejects_non_positive_publish_rate(scene_path: Path):
    rclpy.init(args=[])
    try:
        with pytest.raises(ValueError):
            _make_node(scene_path, publish_rate_hz=0.0)
    finally:
        rclpy.shutdown()


def test_sim_node_rejects_missing_scene_path(tmp_path: Path):
    rclpy.init(args=[])
    try:
        with pytest.raises(FileNotFoundError):
            _make_node(tmp_path / "does-not-exist.xml")
    finally:
        rclpy.shutdown()
