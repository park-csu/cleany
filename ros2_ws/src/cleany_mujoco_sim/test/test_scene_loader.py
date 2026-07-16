import math
from pathlib import Path

import mujoco
import pytest

from cleany_mujoco_sim.scene_loader import load_model


def test_load_model_from_xml_path(scene_path: Path):
    model, data = load_model(scene_path)

    assert model.njnt == 2
    mujoco.mj_step(model, data)
    assert data.time > 0.0


def test_xlerobot_scene_has_articulated_mecanum_rollers():
    scene_path = Path(__file__).parents[1] / 'hardware' / 'scene.xml'
    model, data = load_model(scene_path)

    wheel_prefixes = ('rear_left', 'rear_right', 'front_left', 'front_right')
    roller_count = 0
    for prefix in wheel_prefixes:
        for index in range(12):
            roller_name = f'{prefix}_roller_{index:02d}'
            body_id = mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_BODY, roller_name
            )
            joint_id = mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_JOINT, f'{roller_name}_joint'
            )

            assert body_id >= 0
            assert joint_id >= 0
            assert model.jnt_type[joint_id] == mujoco.mjtJoint.mjJNT_HINGE
            assert model.body_geomnum[body_id] == 1

            geom_id = model.body_geomadr[body_id]
            assert model.geom_type[geom_id] == mujoco.mjtGeom.mjGEOM_CAPSULE
            assert model.geom_condim[geom_id] == 6
            assert model.geom_friction[geom_id, 2] > 0.0
            roller_count += 1

    assert roller_count == 48

    drive_actuators = {
        'rear_left_drive': 'left_wheel_joint',
        'rear_right_drive': 'right_wheel_joint',
        'front_left_drive': 'front_left_wheel_joint',
        'front_right_drive': 'front_right_wheel_joint',
    }
    for actuator_name, joint_name in drive_actuators.items():
        actuator_id = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_ACTUATOR, actuator_name
        )
        joint_id = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_JOINT, joint_name
        )

        assert actuator_id >= 0
        assert joint_id >= 0
        assert model.actuator_dyntype[actuator_id] == mujoco.mjtDyn.mjDYN_DCMOTOR
        assert model.actuator_trntype[actuator_id] == mujoco.mjtTrn.mjTRN_JOINT
        assert model.actuator_trnid[actuator_id, 0] == joint_id
        assert model.actuator_ctrlrange[actuator_id] == pytest.approx((-10.8, 10.8))
        assert model.actuator_forcerange[actuator_id] == pytest.approx(
            (-2.646, 2.646)
        )
        assert model.jnt_actfrcrange[joint_id] == pytest.approx((-2.646, 2.646))

    rear_left_drive_id = mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_ACTUATOR, 'rear_left_drive'
    )
    rear_left_joint_id = mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_JOINT, 'left_wheel_joint'
    )
    rear_left_dof_id = model.jnt_dofadr[rear_left_joint_id]

    # The 10 percent derated rated point remains on the motor curve.
    data.ctrl[rear_left_drive_id] = 10.8
    data.qvel[rear_left_dof_id] = 0.9 * 103.0 * 2.0 * math.pi / 60.0
    mujoco.mj_forward(model, data)
    assert data.actuator_force[rear_left_drive_id] == pytest.approx(2.646, rel=1e-6)

    # At 90 percent voltage, the no-load equilibrium speed also scales by 0.9.
    data.qvel[rear_left_dof_id] = 0.9 * (7000.0 / 61.0) * 2.0 * math.pi / 60.0
    mujoco.mj_forward(model, data)
    assert data.actuator_force[rear_left_drive_id] == pytest.approx(0.0, abs=1e-6)

    mujoco.mj_resetData(model, data)
    chassis_id = mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_BODY, 'chassis'
    )
    assert chassis_id >= 0

    strafe_voltage = {
        'rear_left_drive': 1.0,
        'rear_right_drive': -1.0,
        'front_left_drive': -1.0,
        'front_right_drive': 1.0,
    }
    for actuator_name, voltage in strafe_voltage.items():
        actuator_id = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_ACTUATOR, actuator_name
        )
        data.ctrl[actuator_id] = voltage
    for _ in range(250):
        mujoco.mj_step(model, data)

    assert abs(data.xpos[chassis_id, 1]) > 0.01


def test_xlerobot_arm_uses_feetech_servo_limits_and_speeds():
    scene_path = Path(__file__).parents[1] / 'hardware' / 'scene.xml'
    model, _ = load_model(scene_path)

    servo_specs = (
        (
            2.6477955,
            0.9 * (math.pi / 3.0) / 0.222,
            (
                ('Rotation_L', 'Rotation_L'),
                ('Wrist_Pitch_L', 'Wrist_Pitch_L'),
                ('Wrist_Roll_L', 'Wrist_Roll_L'),
                ('Jaw_L', 'Jaw_L'),
                ('Rotation_R', 'Rotation_R'),
                ('Wrist_Pitch_R', 'Wrist_Pitch_R'),
                ('Wrist_Roll_R', 'Wrist_Roll_R'),
                ('Jaw_R', 'Jaw_R'),
                ('head_pan_joint', 'head_pan'),
                ('head_tilt_joint', 'head_tilt'),
            ),
        ),
        (
            4.4129925,
            0.9 * (math.pi / 3.0) / 0.133,
            (
                ('Pitch_L', 'Pitch_L'),
                ('Elbow_L', 'Elbow_L'),
                ('Pitch_R', 'Pitch_R'),
                ('Elbow_R', 'Elbow_R'),
            ),
        ),
    )

    for stall_torque, no_load_speed, assignments in servo_specs:
        for joint_name, actuator_name in assignments:
            joint_id = mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_JOINT, joint_name
            )
            actuator_id = mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_ACTUATOR, actuator_name
            )
            dof_id = model.jnt_dofadr[joint_id]

            assert joint_id >= 0
            assert actuator_id >= 0
            assert model.actuator_trnid[actuator_id, 0] == joint_id
            assert model.actuator_forcerange[actuator_id] == pytest.approx(
                (-stall_torque, stall_torque)
            )
            assert model.jnt_actfrcrange[joint_id] == pytest.approx(
                (-stall_torque, stall_torque)
            )
            assert model.actuator_gainprm[actuator_id, 0] == pytest.approx(998.22)
            assert model.actuator_biasprm[actuator_id, 2] == pytest.approx(-2.731)

            modeled_no_load_speed = (
                stall_torque - model.dof_frictionloss[dof_id]
            ) / model.dof_damping[dof_id]
            assert modeled_no_load_speed == pytest.approx(no_load_speed, rel=1e-6)
