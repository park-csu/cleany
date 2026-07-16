"""Image conversion helpers for Cleany perception.

Turns a sensor_msgs/Image into an RGB ndarray for the detector. Kept separate
from the ROS node so it can be unit tested without a running graph
(AGENTS.md section 4).

Uses numpy directly instead of cv_bridge: rgb8 unpacking is trivial and this
avoids the cv_bridge/pip-opencv ABI conflict with the ultralytics/torch stack
that lives in this same process.
"""

from __future__ import annotations

import numpy as np
from sensor_msgs.msg import Image


def image_to_ndarray(msg: Image) -> np.ndarray:
    """Convert an rgb8 sensor_msgs/Image into an HxWx3 uint8 RGB ndarray."""
    if msg.encoding != 'rgb8':
        raise ValueError(f"unsupported encoding {msg.encoding!r}, expected 'rgb8'")
    return np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, 3)
