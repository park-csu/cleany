"""Image conversion helpers for Cleany perception.

Thin cv_bridge wrapper turning a sensor_msgs/Image into an RGB ndarray for the
detector. Kept separate from the ROS node so it can be unit tested without a
running graph (AGENTS.md section 4).
"""

from __future__ import annotations

import numpy as np
from cv_bridge import CvBridge
from sensor_msgs.msg import Image

_CV_BRIDGE = CvBridge()


def image_to_ndarray(msg: Image) -> np.ndarray:
    """Convert a sensor_msgs/Image into an HxWx3 uint8 RGB ndarray."""
    return _CV_BRIDGE.imgmsg_to_cv2(msg, desired_encoding='rgb8')
