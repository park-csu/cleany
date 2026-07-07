from __future__ import annotations
from functools import lru_cache

import mujoco
from rclpy.time import Time
from sensor_msgs.msg import JointState

_SCALAR_JOINT_TYPES = (mujoco.mjtJoint.mjJNT_HINGE, mujoco.mjtJoint.mjJNT_SLIDE)


@lru_cache(maxsize=None)
def actuated_joint_ids(model: mujoco.MjModel) -> list[int]:
    return [i for i in range(model.njnt) if model.jnt_type[i] in _SCALAR_JOINT_TYPES]


@lru_cache(maxsize=None)
def steps_per_tick(timestep: float, publish_rate_hz: float) -> int:
    return max(1, round((1.0 / publish_rate_hz) / timestep))


@lru_cache(maxsize=None)
def actuated_joint_names(model: mujoco.MjModel) -> list[str]:
    return [
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
        for i in actuated_joint_ids(model)
    ]


def joint_positions(model: mujoco.MjModel, data: mujoco.MjData) -> list[float]:
    return [float(data.qpos[model.jnt_qposadr[i]]) for i in actuated_joint_ids(model)]


def joint_state_msg(
    model: mujoco.MjModel, data: mujoco.MjData, stamp: Time
) -> JointState:
    msg = JointState()
    msg.header.stamp = stamp.to_msg()
    msg.name = actuated_joint_names(model)
    msg.position = joint_positions(model, data)
    return msg


def apply_joint_cmd(
    model: mujoco.MjModel, data: mujoco.MjData, msg: JointState
) -> None:
    name_to_qposadr = {
        mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i): model.jnt_qposadr[i]
        for i in actuated_joint_ids(model)
    }
    for name, position in zip(msg.name, msg.position):
        qposadr = name_to_qposadr.get(name)
        if qposadr is not None:
            data.qpos[qposadr] = position
