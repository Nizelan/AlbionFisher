"""Bang-bang minigame controller tests (SPEC §5 mechanics)."""

from albionfisher.config.settings import MinigameCfg
from albionfisher.fsm.minigame import MinigameAction, decide

# Zone: width 100, center x = 150. deadzone = 10 px, hysteresis = 5 px.
CFG = MinigameCfg(deadzone_frac=0.1, hysteresis_frac=0.05)
ZONE = (100.0, 0.0, 200.0, 10.0)


def float_at(center_x: float) -> tuple[float, float, float, float]:
    return (center_x - 5.0, 0.0, center_x + 5.0, 10.0)


def test_float_far_left_holds():
    # Float drifts left on its own; left of zone -> hold LMB to push right.
    assert decide(float_at(120.0), ZONE, CFG, currently_holding=False) is MinigameAction.HOLD
    assert decide(float_at(120.0), ZONE, CFG, currently_holding=True) is MinigameAction.HOLD


def test_float_far_right_releases():
    assert decide(float_at(180.0), ZONE, CFG, currently_holding=True) is MinigameAction.RELEASE
    assert decide(float_at(180.0), ZONE, CFG, currently_holding=False) is MinigameAction.RELEASE


def test_float_inside_deadzone_keeps_current_state():
    for cx in (145.0, 150.0, 155.0):  # within +/-10 px deadzone
        assert decide(float_at(cx), ZONE, CFG, currently_holding=False) is MinigameAction.KEEP
        assert decide(float_at(cx), ZONE, CFG, currently_holding=True) is MinigameAction.KEEP


def test_hysteresis_prevents_flip_just_past_deadzone():
    # 12 px right of center: past the deadzone (10) but not past deadzone+hysteresis (15).
    assert decide(float_at(162.0), ZONE, CFG, currently_holding=True) is MinigameAction.KEEP
    # Not holding: no flip needed, releasing is the current behaviour.
    assert decide(float_at(162.0), ZONE, CFG, currently_holding=False) is MinigameAction.RELEASE

    # Mirror case: 12 px left of center.
    assert decide(float_at(138.0), ZONE, CFG, currently_holding=False) is MinigameAction.KEEP
    assert decide(float_at(138.0), ZONE, CFG, currently_holding=True) is MinigameAction.HOLD


def test_flip_happens_past_deadzone_plus_hysteresis():
    assert decide(float_at(166.0), ZONE, CFG, currently_holding=True) is MinigameAction.RELEASE
    assert decide(float_at(134.0), ZONE, CFG, currently_holding=False) is MinigameAction.HOLD


def test_missing_zone_or_float_releases():
    assert decide(float_at(150.0), None, CFG, currently_holding=True) is MinigameAction.RELEASE
    assert decide(None, ZONE, CFG, currently_holding=True) is MinigameAction.RELEASE
    assert decide(None, None, CFG, currently_holding=False) is MinigameAction.RELEASE
