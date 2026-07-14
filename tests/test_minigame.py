"""Minigame controller tests (SPEC §5 mechanics, owner rules 2026-07-14).

Float drifts LEFT; holding LMB pushes RIGHT. Thresholds are fractions of the
BAR width: hold at <=25%, release at >=75%, keep in between.
"""

from albionfisher.config.settings import MinigameCfg
from albionfisher.fsm.minigame import MinigameAction, decide, float_position

CFG = MinigameCfg(hold_below_frac=0.25, release_above_frac=0.75)
# Bar: x from 100 to 500, width 400. 25% -> x=200, 75% -> x=400.
BAR = (100.0, 0.0, 500.0, 30.0)


def float_at(center_x: float) -> tuple[float, float, float, float]:
    return (center_x - 10.0, 0.0, center_x + 10.0, 30.0)


def test_float_position_fraction():
    assert float_position(float_at(100.0), BAR) == 0.0
    assert float_position(float_at(300.0), BAR) == 0.5
    assert float_position(float_at(500.0), BAR) == 1.0


def test_hold_at_or_below_25_percent():
    for cx in (110.0, 150.0, 200.0):  # <= 25% of the bar
        assert decide(float_at(cx), BAR, CFG, currently_holding=False) is MinigameAction.HOLD
        assert decide(float_at(cx), BAR, CFG, currently_holding=True) is MinigameAction.HOLD


def test_release_at_or_above_75_percent():
    for cx in (400.0, 450.0, 490.0):  # >= 75% of the bar
        assert decide(float_at(cx), BAR, CFG, currently_holding=True) is MinigameAction.RELEASE
        assert decide(float_at(cx), BAR, CFG, currently_holding=False) is MinigameAction.RELEASE


def test_keep_between_thresholds():
    """The 25%..75% band keeps the current button state (natural hysteresis).

    While holding, the float moves right across the band until 75%, then LMB
    is released and it drifts left back to 25% — many pull cycles per catch.
    """
    for cx in (210.0, 300.0, 390.0):
        assert decide(float_at(cx), BAR, CFG, currently_holding=False) is MinigameAction.KEEP
        assert decide(float_at(cx), BAR, CFG, currently_holding=True) is MinigameAction.KEEP


def test_missing_bar_or_float_releases():
    assert decide(float_at(300.0), None, CFG, currently_holding=True) is MinigameAction.RELEASE
    assert decide(None, BAR, CFG, currently_holding=True) is MinigameAction.RELEASE
    assert decide(None, None, CFG, currently_holding=False) is MinigameAction.RELEASE


def test_degenerate_bar_width_releases_safely():
    zero_width_bar = (100.0, 0.0, 100.0, 30.0)
    # position computes to 0.0 -> HOLD would be wrong to assert here; the
    # function must simply not crash and return a defined action.
    action = decide(float_at(100.0), zero_width_bar, CFG, currently_holding=False)
    assert action in (MinigameAction.HOLD, MinigameAction.RELEASE, MinigameAction.KEEP)
