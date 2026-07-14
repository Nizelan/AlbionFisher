"""YOLO detector wrapper with a Null fallback when weights are missing.

``ultralytics``/``torch`` are imported lazily inside ``YoloDetector.load`` so
importing this module (and running unit tests) never requires them.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from albionfisher.detection.types import CLASS_NAMES, Detection

if TYPE_CHECKING:
    import numpy as np

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DetectorStatus:
    ok: bool
    message: str


class Detector(Protocol):
    def infer(self, frame: "np.ndarray") -> list[Detection]: ...

    @property
    def status(self) -> DetectorStatus: ...


class NullDetector:
    """Used when model weights are absent/broken: app runs degraded, no crash."""

    def __init__(self, message: str) -> None:
        self._status = DetectorStatus(ok=False, message=message)

    def infer(self, frame: "np.ndarray") -> list[Detection]:
        return []

    @property
    def status(self) -> DetectorStatus:
        return self._status


class YoloDetector:
    """Thin wrapper around an ultralytics YOLO model."""

    def __init__(self, model_path: "str | Path", conf_threshold: float = 0.5) -> None:
        self._model_path = Path(model_path)
        self._conf_threshold = conf_threshold
        self._model = None
        self._status = DetectorStatus(ok=False, message="model not loaded yet")

    def load(self) -> DetectorStatus:
        try:
            from ultralytics import YOLO  # lazy heavy import (pulls in torch)

            self._model = YOLO(str(self._model_path))
            names = getattr(self._model, "names", {}) or {}
            from albionfisher.detection import class_contract

            try:
                contract = class_contract.load_contract()
                warnings = class_contract.verify(contract, names)
            except class_contract.ClassContractError as exc:
                warnings = [str(exc)]
            if warnings:
                for warning in warnings:
                    log.warning("class contract: %s", warning)
                self._status = DetectorStatus(
                    ok=True, message="model loaded with warnings: " + "; ".join(warnings)
                )
            else:
                self._status = DetectorStatus(ok=True, message="model loaded, classes OK")
        except Exception as exc:
            self._model = None
            self._status = DetectorStatus(ok=False, message=f"failed to load model: {exc}")
        return self._status

    def infer(self, frame: "np.ndarray") -> list[Detection]:
        # NEEDS-MODEL: real inference quality can only be verified with the
        # owner-trained weights in model/albionfisher.pt.
        if self._model is None:
            return []
        results = self._model.predict(
            frame, conf=self._conf_threshold, verbose=False
        )
        detections: list[Detection] = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for i in range(len(boxes)):
                class_id = int(boxes.cls[i].item())
                detections.append(
                    Detection(
                        class_id=class_id,
                        class_name=CLASS_NAMES.get(class_id, f"class_{class_id}"),
                        bbox=tuple(float(v) for v in boxes.xyxy[i].tolist()),
                        conf=float(boxes.conf[i].item()),
                    )
                )
        return detections

    @property
    def status(self) -> DetectorStatus:
        return self._status


def create_detector(model_path: "str | Path", conf_threshold: float = 0.5) -> Detector:
    """Return a loaded YoloDetector, or NullDetector when weights are missing."""
    path = Path(model_path)
    if not path.exists():
        message = f"no model at {path} — detection disabled, drop weights into model/"
        log.warning(message)
        return NullDetector(message)
    detector = YoloDetector(path, conf_threshold)
    status = detector.load()
    if not status.ok:
        log.error(status.message)
        return NullDetector(status.message)
    return detector
