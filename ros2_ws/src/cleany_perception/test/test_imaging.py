import numpy as np
from cv_bridge import CvBridge

from cleany_perception.imaging import image_to_ndarray


def test_image_to_ndarray_round_trips_rgb8():
    pixels = np.zeros((4, 6, 3), dtype=np.uint8)
    pixels[0, 0] = (255, 0, 0)
    pixels[1, 2] = (0, 255, 0)
    msg = CvBridge().cv2_to_imgmsg(pixels, encoding='rgb8')

    out = image_to_ndarray(msg)

    assert out.shape == (4, 6, 3)
    assert out.dtype == np.uint8
    np.testing.assert_array_equal(out, pixels)
