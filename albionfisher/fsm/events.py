"""FSM inputs (DetectionSnapshot) and outputs (Commands).

Commands are plain data — the FSM emits them, the worker executes them
(input via InputController, SetFps/Notify handled by the worker itself).
"""

from dataclasses import dataclass, field

from albionfisher.detection.types import Detection


@dataclass(frozen=True)
class DetectionSnapshot:
    """All detections for one frame."""

    detections: tuple[Detection, ...] = field(default_factory=tuple)

    def best(self, class_id: int) -> Detection | None:
        """Highest-confidence detection of the given class, or None."""
        candidates = [d for d in self.detections if d.class_id == class_id]
        if not candidates:
            return None
        return max(candidates, key=lambda d: d.conf)


@dataclass(frozen=True)
class MoveTo:
    """Move cursor to window-relative pixel coordinates."""

    x: int
    y: int


@dataclass(frozen=True)
class PressLmb:
    """Hold LMB for a fixed duration (cast strength), then release."""

    duration_ms: int


@dataclass(frozen=True)
class ClickLmb:
    """Instant LMB click (hooking)."""


@dataclass(frozen=True)
class HoldLmb:
    """Press and keep LMB down (minigame: move float right)."""


@dataclass(frozen=True)
class ReleaseLmb:
    """Release LMB (minigame: float drifts left)."""


@dataclass(frozen=True)
class SetFps:
    """Ask the worker to change the capture/detection frame rate."""

    fps: int


@dataclass(frozen=True)
class Notify:
    """Report an event for logging/UI (no gameplay effect)."""

    event: str


Command = MoveTo | PressLmb | ClickLmb | HoldLmb | ReleaseLmb | SetFps | Notify
