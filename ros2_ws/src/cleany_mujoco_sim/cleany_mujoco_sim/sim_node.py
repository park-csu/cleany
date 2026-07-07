from __future__ import annotations

from pathlib import Path

import mujoco
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

from cleany_mujoco_sim.scene_loader import default_scene_path, load_model
from cleany_mujoco_sim.state import apply_joint_cmd, joint_state_msg, steps_per_tick


class MujocoSimNode(Node):
    def __init__(self, **kwargs) -> None:
        super().__init__('mujoco_sim', **kwargs)

        self.declare_parameter('scene_path', '')
        self.declare_parameter('publish_rate_hz', 60.0)
        self.declare_parameter('headless', True)

        scene_path_value = self.get_parameter('scene_path').get_parameter_value().string_value
        scene_path = Path(scene_path_value) if scene_path_value else default_scene_path()
        publish_rate_hz = self.get_parameter('publish_rate_hz').get_parameter_value().double_value
        self._headless = self.get_parameter('headless').get_parameter_value().bool_value

        if publish_rate_hz <= 0:
            raise ValueError('publish_rate_hz must be positive')

        if not scene_path.exists():
            raise FileNotFoundError(f'MuJoCo scene XML not found: {scene_path}')

        self._model, self._data = load_model(scene_path)
        self._steps_per_tick = steps_per_tick(self._model.opt.timestep, publish_rate_hz)
        self._joint_state_pub = self.create_publisher(JointState, 'joint_states', 10)
        self.create_subscription(JointState, '~/joint_cmd', self._on_joint_cmd, 10)
        self.create_timer(1.0 / publish_rate_hz, self._on_timer)

        self._viewer = None
        if not self._headless:
            import mujoco.viewer

            self._viewer = mujoco.viewer.launch_passive(self._model, self._data)

    def destroy_node(self) -> bool:
        if self._viewer is not None:
            self._viewer.close()
        return super().destroy_node()

    def _on_joint_cmd(self, msg: JointState) -> None:
        apply_joint_cmd(self._model, self._data, msg)

    def _on_timer(self) -> None:
        for _ in range(self._steps_per_tick):
            mujoco.mj_step(self._model, self._data)
        self._joint_state_pub.publish(
            joint_state_msg(self._model, self._data, self.get_clock().now())
        )
        if self._viewer is not None:
            self._viewer.sync()


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = MujocoSimNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
