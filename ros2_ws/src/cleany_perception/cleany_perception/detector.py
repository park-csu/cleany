"""Pure object-detection logic for Cleany perception.

ROS-independent detection core so it can be unit tested without a running ROS
graph (AGENTS.md section 4). It takes an image (ndarray) and returns detection
candidates; it does not decide robot behaviour (that is the Planner's job).

- `Detection`: a single detection candidate (label, score, pixel bbox).
- `parse_boxes()`: pure conversion of raw box arrays into `Detection`s; unit
  tested without ultralytics.
- `YoloDetector`: wraps an ultralytics YOLO model. `ultralytics` is imported
  lazily so this module (and `parse_boxes`) imports without it installed.

Model choice (YOLO11n, pretrained COCO) is an experiment-branch decision and is
not confirmed in the KB. Weights/conf/classes are configurable, never hardcoded
as project truth (AGENTS.md section 4).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class Detection:
    """One detection candidate. Bbox is pixel corners (x1,y1)-(x2,y2)."""

    label: str
    score: float
    x1: float
    y1: float
    x2: float
    y2: float


def parse_boxes(
    boxes_xyxy: Iterable[Sequence[float]],
    scores: Iterable[float],
    class_ids: Iterable[float],
    class_names: Mapping[int, str] | Sequence[str],
) -> list[Detection]:
    """Turn raw model outputs into Detection candidates (pure).

    `class_names` maps class id -> label (ultralytics `model.names` is a dict).
    Unknown ids fall back to their stringified id rather than raising, so an
    unexpected class never crashes perception.
    """
    detections: list[Detection] = []
    for (x1, y1, x2, y2), score, class_id in zip(boxes_xyxy, scores, class_ids):
        cid = int(class_id)
        try:
            label = class_names[cid]
        except (KeyError, IndexError):
            label = str(cid)
        detections.append(
            Detection(
                label=str(label),
                score=float(score),
                x1=float(x1),
                y1=float(y1),
                x2=float(x2),
                y2=float(y2),
            )
        )
    return detections


class YoloDetector:
    """ultralytics YOLO wrapper. Loads the model lazily on first detect()."""

    def __init__(
        self,
        weights: str = 'yolo11n.pt',
        conf: float = 0.25,
        classes: Sequence[int] | None = None,
    ) -> None:
        self._weights = weights
        self._conf = conf
        self._classes = list(classes) if classes is not None else None
        self._model = None

    def _ensure_model(self) -> None:
        if self._model is None:
            from ultralytics import YOLO

            self._model = YOLO(self._weights)

    def detect(self, image) -> list[Detection]:
        """Run detection on an RGB ndarray and return Detection candidates."""
        self._ensure_model()
        results = self._model.predict(
            source=image,
            conf=self._conf,
            classes=self._classes,
            verbose=False,
        )
        if not results:
            return []
        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return []
        xyxy = boxes.xyxy.cpu().numpy()
        scores = boxes.conf.cpu().numpy()
        class_ids = boxes.cls.cpu().numpy()
        return parse_boxes(xyxy, scores, class_ids, self._model.names)
