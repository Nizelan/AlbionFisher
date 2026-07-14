"""Bang-bang minigame controller with hysteresis (SPEC §5).

Mechanic (confirmed by owner): the float always drifts LEFT on its own;
holding LMB moves it RIGHT. So:

- float center left of zone center minus deadzone  -> HOLD (push right)
- float center right of zone center plus deadzone  -> RELEASE (drift left)
- inside the deadzone                              -> KEEP (no button change)

Hysteresis widens the threshold for *flipping* the current button state, so a
float hovering exactly at a deadzone edge does not cause rapid toggling.
Missing zone/float bbox -> RELEASE (fail safe; caller reports the loss).
"""

from enum import Enum

from albionfisher.config.settings import MinigameCfg

BBox = tuple[float, float, float, float]


class MinigameAction(Enum):
    HOLD = "HOLD"
    RELEASE = "RELEASE"
    KEEP = "KEEP"


def _center_x(bbox: BBox) -> float:
    return (bbox[0] + bbox[2]) / 2.0


def decide(
    float_bbox: BBox | None,
    zone_bbox: BBox | None,
    cfg: MinigameCfg,
    currently_holding: bool,
) -> MinigameAction:
    if zone_bbox is None or float_bbox is None:
        return MinigameAction.RELEASE

    zone_width = zone_bbox[2] - zone_bbox[0]
    deadzone = cfg.deadzone_frac * zone_width
    hysteresis = cfg.hysteresis_frac * zone_width
    offset = _center_x(float_bbox) - _center_x(zone_bbox)  # >0: float right of center

    if currently_holding:
        # Flipping to RELEASE requires passing the deadzone plus hysteresis.
        if offset > deadzone + hysteresis:
            return MinigameAction.RELEASE
        if offset < -deadzone:
            return MinigameAction.HOLD
        return MinigameAction.KEEP

    # Not holding: flipping to HOLD requires passing deadzone plus hysteresis.
    if offset < -(deadzone + hysteresis):
        return MinigameAction.HOLD
    if offset > deadzone:
        return MinigameAction.RELEASE
    return MinigameAction.KEEP
