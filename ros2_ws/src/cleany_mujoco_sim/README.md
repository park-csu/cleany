# cleany_mujoco_sim

ROS 2 (ament_python) package wrapping the XLeRobot MuJoCo simulation.

## Run

    ros2 launch cleany_mujoco_sim mujoco_sim.launch.py headless:=false

## Topics

- Publishes `joint_states` (`sensor_msgs/JointState`)
- Subscribes `~/joint_cmd` (`sensor_msgs/JointState`) — sets target joint
  positions directly (no controller yet)

## Scope

Minimal ROS 2 integration only. Binding to `cleany_robot_interface` /
`cleany_perception` / the mission FSM is a separate, later task once those
packages define their interfaces.
