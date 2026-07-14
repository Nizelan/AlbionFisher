"""Minigame controller: keep the float inside the bar (SPEC §5).

Mechanic (confirmed by owner): the float starts at the center of the bar,
constantly drifts LEFT trying to escape the left edge; holding LMB pushes it
RIGHT. The fish is pulled ashore only while LMB is held, so the controller
naturally alternates hold/release many times per catch.

Control rule (owner, 2026-07-14) — thresholds are fractions of the BAR width:

- float position <= hold_below_frac  (default 25%) -> HOLD (push right)
- float position >= release_above_frac (default 75%) -> RELEASE (drift left)
- in between -> KEEP current button state

The wide 25%..75% band acts as natural hysteresis: no rapid toggling.
Missing bar/float bbox -> RELEASE (fail safe; caller reports it).
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


def float_position(float_bbox: BBox, bar_bbox: BBox) -> float:
    """Float center as a 0..1 fraction of the bar width (0 = left edge)."""
    bar_left = bar_bbox[0]
    bar_width = bar_bbox[2] - bar_bbox[0]
    if bar_width <= 0:
        return 0.0
    return (_center_x(float_bbox) - bar_left) / bar_width


def decide(
    float_bbox: BBox | None,
    bar_bbox: BBox | None,
    cfg: MinigameCfg,
    currently_holding: bool,
) -> MinigameAction:
    if bar_bbox is None or float_bbox is None:
        return MinigameAction.RELEASE

    position = float_position(float_bbox, bar_bbox)
    if position <= cfg.hold_below_frac:
        return MinigameAction.HOLD
    if position >= cfg.release_above_frac:
        return MinigameAction.RELEASE
    return MinigameAction.KEEP
