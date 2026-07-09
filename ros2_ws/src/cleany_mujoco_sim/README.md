# cleany_mujoco_sim

ROS 2 (ament_python) package wrapping the XLeRobot MuJoCo simulation.

## Run

Headless simulation:

```bash
ros2 launch cleany_mujoco_sim mujoco_sim.launch.py
```

Simulation with the MuJoCo viewer:

```bash
ros2 launch cleany_mujoco_sim mujoco_sim.launch.py headless:=false
```

## Topics

`mujoco_sim_node` publishes:

- `joint_states` (`sensor_msgs/JointState`)
- `odom` (`nav_msgs/Odometry`)
- `scan` (`sensor_msgs/LaserScan`)
- `tf` (`odom` -> `base_link`) when `publish_odom_tf` is true
- `tf_static` (`base_link` -> `laser`) when laser scan publishing is enabled

`mujoco_sim_node` subscribes:

- `~/joint_cmd` (`sensor_msgs/JointState`) - sets target joint positions
  directly. This is a simple simulation hook, not a controller.

There is not yet a `/cmd_vel` base command interface. The current MuJoCo base
model still uses the existing wheel setup in `hardware/xlerobot.xml`; mecanum
base support needs a separate model and command adapter change.

## Launch Arguments

`mujoco_sim.launch.py`:

- `scene_path` - MuJoCo scene XML. Defaults to `hardware/scene.xml`.
- `publish_rate_hz` - simulation publish/timer rate. Defaults to `60.0`.
- `headless` - whether to hide the MuJoCo viewer. Defaults to `true`.
- `scan_rate_hz` - laser scan publish rate. Defaults to `5.5`.
- `scan_samples` - number of rays per scan. `0` derives the sample count from
  `scan_sample_rate_hz`.

Additional node parameters supported by `MujocoSimNode`:

- `base_body_name` - MuJoCo body used as the robot base. Defaults to `chassis`.
- `lidar_site_name` - MuJoCo site used as the laser origin. Defaults to
  `lidar_site`.
- `odom_frame_id` - odometry frame id. Defaults to `odom`.
- `base_frame_id` - base frame id. Defaults to `base_link`.
- `laser_frame_id` - laser frame id. Defaults to `laser`.
- `publish_odom_tf` - publish dynamic odom-to-base transform. Defaults to
  `true`.
- `scan_enabled` - publish `scan` and static laser transform. Defaults to
  `true`.
- `scan_sample_rate_hz` - virtual ray sample rate used when `scan_samples` is
  `0`. Defaults to `8000.0`.
- `scan_range_min` - minimum valid scan range. Defaults to `0.15`.
- `scan_range_max` - maximum valid scan range. Defaults to `12.0`.

## Scope

This package is still a simulation bridge, not the full robot interface.

Implemented:

- Load an XLeRobot MuJoCo scene.
- Step the simulator on a ROS timer.
- Publish joint state, odometry, laser scan, and TF data.
- Apply direct joint position commands for simulation tests.

Not implemented yet:

- `/cmd_vel` or Nav2-compatible base command handling.
- A mecanum wheel kinematic or physical base adapter.
- Binding to `cleany_robot_interface`, `cleany_perception`, or the mission FSM.
- Hardware-realistic controllers for the base or manipulators.
