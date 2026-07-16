import numpy as np
from sensor_msgs.msg import Image

from cleany_perception.imaging import image_to_ndarray


def _rgb8_msg(pixels: np.ndarray) -> Image:
    pixels = np.ascontiguousarray(pixels, dtype=np.uint8)
    height, width = pixels.shape[:2]
    msg = Image()
    msg.height = height
    msg.width = width
    msg.encoding = 'rgb8'
    msg.is_bigendian = 0
    msg.step = width * 3
    msg.data = pixels.tobytes()
    return msg


def test_image_to_ndarray_round_trips_rgb8():
    pixels = np.zeros((4, 6, 3), dtype=np.uint8)
    pixels[0, 0] = (255, 0, 0)
    pixels[1, 2] = (0, 255, 0)
    msg = _rgb8_msg(pixels)

    out = image_to_ndarray(msg)

    assert out.shape == (4, 6, 3)
    assert out.dtype == np.uint8
    np.testing.assert_array_equal(out, pixels)
