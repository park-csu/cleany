"""ROS 2 node wrapper for Cleany perception.

Thin ROS layer over the pure logic in detector.py: subscribes to a camera
Image topic, runs detection, and publishes detection candidates. All detection
logic lives in detector.py so it stays unit-testable without ROS.

Not implemented yet. Filled in Step 6, which will:
- subscribe to the sim/robot Image topic (e.g. /image_raw from cleany_mujoco_sim),
- convert with imaging.image_to_ndarray() and call detector.detect(),
- publish the detection result message (type decided in Step 4),
- register a `detection_node` console_scripts entry point in setup.py.
"""

from __future__ import annotations

# TODO(step-6): implement main() (Image sub -> detector.detect -> publish) and
# register the entry point in setup.py.
