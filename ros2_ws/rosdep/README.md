# Cleany rosdep rules

`mujoco` isn't in the default rosdep database, so this workspace ships its
own rule file. Register it once per machine:

    sudo sh -c 'echo "yaml file://'"$(pwd)"'/ros2_ws/rosdep/cleany.yaml" > /etc/ros/rosdep/sources.list.d/10-cleany.list'
    rosdep update

Then install workspace dependencies as usual:

    rosdep install --from-paths ros2_ws/src --ignore-src -r -y
