"""Convert Detection candidates into vision_msgs (AGENTS.md section 3).

Perception publishes generic detection candidates; it does not encode
collect/skip semantics (that is the Planner's job). We reuse the standard
vision_msgs/Detection2DArray so downstream tools interoperate and a 3D pose
slot is already available for a later depth stage.
"""

from __future__ import annotations

from typing import Iterable

from rclpy.time import Time
from vision_msgs.msg import (
    BoundingBox2D,
    Detection2D,
    Detection2DArray,
    ObjectHypothesisWithPose,
)

from cleany_perception.detector import Detection


def detection_to_msg(det: Detection, stamp: Time, frame_id: str) -> Detection2D:
    msg = Detection2D()
    msg.header.stamp = stamp.to_msg()
    msg.header.frame_id = frame_id

    hypothesis = ObjectHypothesisWithPose()
    hypothesis.hypothesis.class_id = det.label
    hypothesis.hypothesis.score = det.score
    msg.results.append(hypothesis)

    bbox = BoundingBox2D()
    bbox.center.position.x = (det.x1 + det.x2) / 2.0
    bbox.center.position.y = (det.y1 + det.y2) / 2.0
    bbox.center.theta = 0.0
    bbox.size_x = det.x2 - det.x1
    bbox.size_y = det.y2 - det.y1
    msg.bbox = bbox
    return msg


def detections_to_msg(
    detections: Iterable[Detection], stamp: Time, frame_id: str
) -> Detection2DArray:
    msg = Detection2DArray()
    msg.header.stamp = stamp.to_msg()
    msg.header.frame_id = frame_id
    msg.detections = [detection_to_msg(det, stamp, frame_id) for det in detections]
    return msg
