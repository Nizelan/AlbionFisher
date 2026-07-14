"""Detection result type and class-ID constants.

IDs mirror ``model/classes.yaml`` — the single source of truth (SPEC §4).
``class_contract.verify`` checks the loaded model against that file at runtime.
"""

from dataclasses import dataclass

FISHING_ZONE = 0
BOBBER_IDLE = 1
BOBBER_BITE = 2
MINIGAME_BAR = 3
MINIGAME_FLOAT = 4
MINIGAME_ZONE = 5
CATCH_POPUP = 6

CLASS_NAMES: dict[int, str] = {
    FISHING_ZONE: "fishing_zone",
    BOBBER_IDLE: "bobber_idle",
    BOBBER_BITE: "bobber_bite",
    MINIGAME_BAR: "minigame_bar",
    MINIGAME_FLOAT: "minigame_float",
    MINIGAME_ZONE: "minigame_zone",
    CATCH_POPUP: "catch_popup",
}


@dataclass(frozen=True)
class Detection:
    class_id: int
    class_name: str
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2 in frame pixels
    conf: float

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return (x1 + x2) / 2.0, (y1 + y2) / 2.0

    @property
    def width(self) -> float:
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> float:
        return self.bbox[3] - self.bbox[1]
