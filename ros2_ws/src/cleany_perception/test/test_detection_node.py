import numpy as np
import pytest
import rclpy
from sensor_msgs.msg import Image

from cleany_perception.detection_node import DetectionNode
from cleany_perception.detector import Detection


class _FakeDetector:
    """Stand-in for YoloDetector: records calls, returns canned detections."""

    def __init__(self, detections):
        self._detections = detections
        self.loaded = False
        self.last_image = None

    def load(self):
        self.loaded = True

    def detect(self, image):
        self.last_image = image
        return self._detections


def _rgb8_msg(height=4, width=6, frame_id='head_camera_rgb_optical_frame') -> Image:
    pixels = np.zeros((height, width, 3), dtype=np.uint8)
    msg = Image()
    msg.header.frame_id = frame_id
    msg.height = height
    msg.width = width
    msg.encoding = 'rgb8'
    msg.is_bigendian = 0
    msg.step = width * 3
    msg.data = pixels.tobytes()
    return msg


@pytest.fixture
def ros():
    rclpy.init()
    yield
    rclpy.shutdown()


def test_node_warms_up_detector_on_construction(ros):
    fake = _FakeDetector([])
    node = DetectionNode(detector=fake)
    try:
        assert fake.loaded is True
    finally:
        node.destroy_node()


def test_detect_on_wires_image_through_detector_to_msg(ros):
    dets = [
        Detection(label='cup', score=0.9, x1=10.0, y1=20.0, x2=30.0, y2=60.0),
        Detection(label='bottle', score=0.5, x1=0.0, y1=0.0, x2=4.0, y2=4.0),
    ]
    fake = _FakeDetector(dets)
    node = DetectionNode(detector=fake)
    try:
        out = node.detect_on(_rgb8_msg())

        # detector received a decoded HxWx3 ndarray
        assert fake.last_image.shape == (4, 6, 3)
        # frame_id passes through from the source image
        assert out.header.frame_id == 'head_camera_rgb_optical_frame'
        # both detections mapped into the array with correct labels
        assert len(out.detections) == 2
        assert [d.results[0].hypothesis.class_id for d in out.detections] == ['cup', 'bottle']
        assert out.detections[0].bbox.center.position.x == 20.0
        assert out.detections[0].bbox.size_x == 20.0
    finally:
        node.destroy_node()


def test_detect_on_empty_detections_yields_empty_array(ros):
    fake = _FakeDetector([])
    node = DetectionNode(detector=fake)
    try:
        out = node.detect_on(_rgb8_msg())

        assert out.detections == []
        assert out.header.frame_id == 'head_camera_rgb_optical_frame'
    finally:
        node.destroy_node()
