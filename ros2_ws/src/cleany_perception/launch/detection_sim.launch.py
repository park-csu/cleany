"""End-to-end launch: MuJoCo sim + YOLO detection node.

Starts cleany_mujoco_sim (publishes /image_raw) and the perception
detection_node (publishes /detections) together, so the whole pipeline comes
up with one command.

Host-controlled runtime env is intentionally NOT set here (AGENTS.md):
- MUJOCO_GL (egl/osmesa/glfw) -> export before launching.
- CUDA_VISIBLE_DEVICES -> export if you need to hide an unusable GPU.

All detection tuning (weights, conf, device, detection_rate_hz, classes,
publish_annotated, ...) lives in the params file so it stays in one place and
never clobbers itself. To change behaviour, edit config/detection.yaml or pass
your own file with `params_file:=<path>` (e.g. an annotated/GPU variant).
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    headless_arg = DeclareLaunchArgument('headless', default_value='true')
    params_file_arg = DeclareLaunchArgument(
        'params_file',
        default_value=PathJoinSubstitution(
            [FindPackageShare('cleany_perception'), 'config', 'detection.yaml']
        ),
        description='Params file for detection_node.',
    )

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare('cleany_mujoco_sim'), 'launch', 'mujoco_sim.launch.py']
            )
        ),
        launch_arguments={'headless': LaunchConfiguration('headless')}.items(),
    )

    detection = Node(
        package='cleany_perception',
        executable='detection_node',
        name='detection_node',
        parameters=[LaunchConfiguration('params_file')],
        output='screen',
    )

    return LaunchDescription([
        headless_arg,
        params_file_arg,
        sim,
        detection,
    ])
