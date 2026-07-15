from rclpy.time import Time

from cleany_perception.detector import Detection
from cleany_perception.detection_to_msg import detection_to_msg, detections_to_msg


def _sample() -> Detection:
    return Detection(label='cup', score=0.87, x1=10.0, y1=20.0, x2=30.0, y2=60.0)


def test_detection_to_msg_maps_bbox_center_and_size():
    msg = detection_to_msg(_sample(), Time(), 'head_camera_rgb_optical_frame')

    assert msg.header.frame_id == 'head_camera_rgb_optical_frame'
    assert msg.bbox.center.position.x == 20.0
    assert msg.bbox.center.position.y == 40.0
    assert msg.bbox.size_x == 20.0
    assert msg.bbox.size_y == 40.0


def test_detection_to_msg_maps_hypothesis_label_and_score():
    msg = detection_to_msg(_sample(), Time(), 'cam')

    assert len(msg.results) == 1
    assert msg.results[0].hypothesis.class_id == 'cup'
    assert msg.results[0].hypothesis.score == 0.87


def test_detections_to_msg_wraps_all_detections_with_header():
    dets = [
        _sample(),
        Detection(label='bottle', score=0.5, x1=0.0, y1=0.0, x2=4.0, y2=4.0),
    ]

    arr = detections_to_msg(dets, Time(), 'cam')

    assert arr.header.frame_id == 'cam'
    assert len(arr.detections) == 2
    assert [d.results[0].hypothesis.class_id for d in arr.detections] == ['cup', 'bottle']


def test_detections_to_msg_empty_returns_no_detections():
    arr = detections_to_msg([], Time(), 'cam')

    assert arr.detections == []
    assert arr.header.frame_id == 'cam'
