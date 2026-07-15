"""Pure object-detection logic for Cleany perception.

This module holds the ROS-independent detection core so it can be unit tested
without a running ROS graph (see AGENTS.md section 4). It takes an image
(ndarray) and returns detection candidates; it does not decide robot behaviour.

Not implemented yet. Filled in later steps:
- detection model / runtime is still undecided in the KB
  (docs/cleany-docs/10_PLANNING/08 - Questions.md) — do not hardcode a model here.
- Step 4 defines the detection result type (vision_msgs vs custom).
- Step 5 implements the detector and its pytest coverage.
"""

from __future__ import annotations

# TODO(step-5): implement detect(image) -> list[detection candidate] once the
# model (Step 3) and result type (Step 4) are decided.
