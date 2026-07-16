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


def ndarray_to_image_msg(pixels: np.ndarray, header) -> Image:
    """Pack an HxWx3 uint8 RGB ndarray into an rgb8 sensor_msgs/Image.

    Reverse of image_to_ndarray(); used to publish annotated frames. header is
    copied from the source image so the annotated stream stays aligned.
    """
    pixels = np.ascontiguousarray(pixels, dtype=np.uint8)
    height, width = pixels.shape[:2]
    msg = Image()
    msg.header = header
    msg.height = height
    msg.width = width
    msg.encoding = 'rgb8'
    msg.is_bigendian = 0
    msg.step = width * 3
    msg.data = pixels.tobytes()
    return msg
