import numpy as np
from std_msgs.msg import Header
from sensor_msgs.msg import Image

from cleany_perception.imaging import image_to_ndarray, ndarray_to_image_msg


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


def test_ndarray_to_image_msg_round_trips_and_keeps_header():
    pixels = np.zeros((4, 6, 3), dtype=np.uint8)
    pixels[2, 3] = (1, 2, 3)
    header = Header()
    header.frame_id = 'cam'

    msg = ndarray_to_image_msg(pixels, header)

    assert msg.encoding == 'rgb8'
    assert msg.height == 4
    assert msg.width == 6
    assert msg.step == 18
    assert msg.header.frame_id == 'cam'
    np.testing.assert_array_equal(image_to_ndarray(msg), pixels)
