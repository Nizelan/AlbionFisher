"""FSM transition tests (SPEC §5) — pure, synthetic snapshots, injected time."""

from albionfisher.config.settings import Settings, StopCfg
from albionfisher.detection.types import (
    BOBBER_BITE,
    BOBBER_IDLE,
    CATCH_POPUP,
    CLASS_NAMES,
    FISHING_ZONE,
    MINIGAME_BAR,
    MINIGAME_FLOAT,
    MINIGAME_ZONE,
    Detection,
)
from albionfisher.fsm.events import (
    ClickLmb,
    DetectionSnapshot,
    HoldLmb,
    MoveTo,
    Notify,
    PressLmb,
    ReleaseLmb,
    SetFps,
)
from albionfisher.fsm.machine import (
    MAX_CAST_ATTEMPTS,
    POPUP_DRAIN_S,
    RESULT_WINDOW_S,
    FishingFsm,
)
from albionfisher.fsm.states import State

BAR_BBOX = (100.0, 100.0, 500.0, 130.0)
ZONE_BBOX = (280.0, 100.0, 320.0, 130.0)  # centered in the bar, width 40


def det(class_id: int, bbox=(0.0, 0.0, 10.0, 10.0), conf: float = 0.9) -> Detection:
    return Detection(class_id=class_id, class_name=CLASS_NAMES[class_id], bbox=bbox, conf=conf)


def snap(*detections: Detection) -> DetectionSnapshot:
    return DetectionSnapshot(detections=tuple(detections))


EMPTY = snap()


def make_fsm(**stop_overrides) -> FishingFsm:
    settings = Settings()
    if stop_overrides:
        settings.stop = StopCfg(**stop_overrides)
    return FishingFsm(settings)


def to_cast(fsm: FishingFsm, t: float = 0.0) -> float:
    fsm.start(t)
    fsm.step(snap(det(FISHING_ZONE, bbox=(400.0, 300.0, 500.0, 400.0))), t + 1.0)
    assert fsm.state is State.CAST
    return t + 1.0


def to_wait_bite(fsm: FishingFsm, t: float = 0.0) -> float:
    t = to_cast(fsm, t)
    fsm.step(snap(det(BOBBER_IDLE)), t + 1.0)
    assert fsm.state is State.WAIT_BITE
    return t + 1.0


def to_minigame(fsm: FishingFsm, t: float = 0.0) -> float:
    t = to_wait_bite(fsm, t)
    fsm.step(snap(det(BOBBER_BITE)), t + 1.0)
    assert fsm.state is State.HOOK
    fsm.step(snap(det(MINIGAME_BAR, bbox=BAR_BBOX)), t + 2.0)
    assert fsm.state is State.MINIGAME
    return t + 2.0


def fail_one_cycle(fsm: FishingFsm, t: float) -> float:
    """From FIND_ZONE: cast 3 times with no bobber -> one consecutive fail."""
    cast_confirm = fsm._cfg.timeouts.cast_confirm
    fsm.step(snap(det(FISHING_ZONE)), t)
    assert fsm.state is State.CAST
    for _ in range(MAX_CAST_ATTEMPTS):
        t += cast_confirm
        fsm.step(EMPTY, t)
    return t


# -- IDLE / start ------------------------------------------------------------


def test_idle_ignores_detections():
    fsm = make_fsm()
    assert fsm.state is State.IDLE
    assert fsm.step(snap(det(FISHING_ZONE)), 1.0) == []
    assert fsm.state is State.IDLE


def test_start_moves_to_find_zone():
    fsm = make_fsm()
    fsm.start(0.0)
    assert fsm.state is State.FIND_ZONE


# -- FIND_ZONE -----------------------------------------------------------------


def test_find_zone_to_cast_emits_move_and_press():
    fsm = make_fsm()
    fsm.start(0.0)
    zone = det(FISHING_ZONE, bbox=(400.0, 300.0, 500.0, 400.0))
    cmds = fsm.step(snap(zone), 1.0)
    assert fsm.state is State.CAST
    assert MoveTo(450, 350) in cmds
    assert PressLmb(fsm._cfg.cast.hold_ms) in cmds


def test_find_zone_with_bobber_in_water_resumes_wait_bite():
    """Safety guard: never cast while the rod is already in the water."""
    fsm = make_fsm()
    fsm.start(0.0)
    zone = det(FISHING_ZONE, bbox=(400.0, 300.0, 500.0, 400.0))
    cmds = fsm.step(snap(zone, det(BOBBER_IDLE)), 1.0)
    assert fsm.state is State.WAIT_BITE
    assert not any(isinstance(c, PressLmb) for c in cmds)


def test_find_zone_timeout_reports_and_retries():
    fsm = make_fsm()
    fsm.start(0.0)
    timeout = fsm._cfg.timeouts.find_zone
    assert fsm.step(EMPTY, timeout - 0.1) == []
    cmds = fsm.step(EMPTY, timeout)
    assert fsm.state is State.FIND_ZONE
    assert any(isinstance(c, Notify) for c in cmds)
    # timer was reset: no immediate second report
    assert fsm.step(EMPTY, timeout + 0.1) == []


# -- CAST ---------------------------------------------------------------------


def test_cast_confirmed_by_bobber_idle():
    fsm = make_fsm()
    t = to_cast(fsm)
    fsm.step(snap(det(BOBBER_IDLE)), t + 0.5)
    assert fsm.state is State.WAIT_BITE


def test_cast_retries_then_fails_after_max_attempts():
    fsm = make_fsm()
    t = to_cast(fsm)
    cast_confirm = fsm._cfg.timeouts.cast_confirm

    # retries 2 and 3 re-emit the cast press
    for _attempt in (2, 3):
        t += cast_confirm
        cmds = fsm.step(EMPTY, t)
        assert fsm.state is State.CAST
        assert any(isinstance(c, PressLmb) for c in cmds)

    # 4th timeout: attempts exhausted -> fail -> back to FIND_ZONE
    t += cast_confirm
    fsm.step(EMPTY, t)
    assert fsm.state is State.FIND_ZONE
    assert fsm.counters.lost == 1
    assert fsm.consecutive_fails == 1


# -- WAIT_BITE ------------------------------------------------------------------


def test_bite_triggers_hook_with_click():
    fsm = make_fsm()
    t = to_wait_bite(fsm)
    cmds = fsm.step(snap(det(BOBBER_BITE)), t + 1.0)
    assert fsm.state is State.HOOK
    assert ClickLmb() in cmds


def test_bite_timeout_recasts():
    fsm = make_fsm()
    t = to_wait_bite(fsm)
    bite = fsm._cfg.timeouts.bite
    assert fsm.step(EMPTY, t + bite - 0.1) == []
    cmds = fsm.step(EMPTY, t + bite)
    assert fsm.state is State.CAST
    assert fsm.counters.recasts == 1
    assert any(isinstance(c, PressLmb) for c in cmds)


# -- HOOK ------------------------------------------------------------------------


def test_hook_to_minigame_raises_fps():
    fsm = make_fsm()
    t = to_wait_bite(fsm)
    fsm.step(snap(det(BOBBER_BITE)), t + 1.0)
    cmds = fsm.step(snap(det(MINIGAME_BAR, bbox=BAR_BBOX)), t + 1.5)
    assert fsm.state is State.MINIGAME
    assert SetFps(fsm._cfg.detection.minigame_fps) in cmds


def test_hook_timeout_goes_to_result():
    fsm = make_fsm()
    t = to_wait_bite(fsm)
    fsm.step(snap(det(BOBBER_BITE)), t + 1.0)
    fsm.step(EMPTY, t + 1.0 + fsm._cfg.timeouts.minigame_start)
    assert fsm.state is State.RESULT


# -- MINIGAME ----------------------------------------------------------------------


def test_minigame_holds_when_float_left_of_zone():
    fsm = make_fsm()
    t = to_minigame(fsm)
    float_left = det(MINIGAME_FLOAT, bbox=(150.0, 100.0, 170.0, 130.0))
    zone = det(MINIGAME_ZONE, bbox=ZONE_BBOX)
    bar = det(MINIGAME_BAR, bbox=BAR_BBOX)
    cmds = fsm.step(snap(bar, zone, float_left), t + 0.1)
    assert HoldLmb() in cmds
    assert fsm.state is State.MINIGAME


def test_minigame_releases_when_float_right_of_zone():
    fsm = make_fsm()
    t = to_minigame(fsm)
    bar = det(MINIGAME_BAR, bbox=BAR_BBOX)
    zone = det(MINIGAME_ZONE, bbox=ZONE_BBOX)
    float_left = det(MINIGAME_FLOAT, bbox=(150.0, 100.0, 170.0, 130.0))
    fsm.step(snap(bar, zone, float_left), t + 0.1)  # now holding
    float_right = det(MINIGAME_FLOAT, bbox=(430.0, 100.0, 450.0, 130.0))
    cmds = fsm.step(snap(bar, zone, float_right), t + 0.2)
    assert ReleaseLmb() in cmds


def test_minigame_bar_gone_goes_to_result_and_releases():
    fsm = make_fsm()
    t = to_minigame(fsm)
    bar = det(MINIGAME_BAR, bbox=BAR_BBOX)
    zone = det(MINIGAME_ZONE, bbox=ZONE_BBOX)
    float_left = det(MINIGAME_FLOAT, bbox=(150.0, 100.0, 170.0, 130.0))
    fsm.step(snap(bar, zone, float_left), t + 0.1)  # now holding
    cmds = fsm.step(EMPTY, t + 0.2)
    assert fsm.state is State.RESULT
    assert ReleaseLmb() in cmds
    assert SetFps(fsm._cfg.detection.idle_fps) in cmds


def test_minigame_float_escape_counts_as_loss():
    fsm = make_fsm()
    t = to_minigame(fsm)
    bar = det(MINIGAME_BAR, bbox=BAR_BBOX)
    escaped = det(MINIGAME_FLOAT, bbox=(510.0, 100.0, 530.0, 130.0))  # past right edge
    fsm.step(snap(bar, escaped), t + 0.1)
    assert fsm.state is State.RESULT
    fsm.step(EMPTY, t + 0.2)  # RESULT resolves the pending fail immediately
    assert fsm.counters.lost == 1
    assert fsm.state is State.FIND_ZONE


# -- RESULT ---------------------------------------------------------------------------


def test_result_popup_counts_catch_and_loops():
    fsm = make_fsm()
    t = to_minigame(fsm)
    fsm.step(EMPTY, t + 0.1)  # bar gone -> RESULT
    fsm.consecutive_fails = 3
    fsm.step(snap(det(CATCH_POPUP)), t + 0.2)
    assert fsm.counters.caught == 1
    assert fsm.consecutive_fails == 0  # success resets the fail streak
    assert fsm.state is State.RESULT  # draining possible follow-up popups
    fsm.step(EMPTY, t + 0.2 + POPUP_DRAIN_S)
    assert fsm.state is State.FIND_ZONE


def test_result_double_popup_counts_single_catch():
    """Fish + seaweed produce two popups — must count as ONE catch."""
    fsm = make_fsm()
    t = to_minigame(fsm)
    fsm.step(EMPTY, t + 0.1)  # -> RESULT
    fsm.step(snap(det(CATCH_POPUP)), t + 0.2)  # fish popup
    fsm.step(EMPTY, t + 0.5)  # brief gap between popups
    fsm.step(snap(det(CATCH_POPUP)), t + 0.7)  # seaweed popup
    assert fsm.counters.caught == 1  # not 2
    assert fsm.state is State.RESULT
    # drain window elapses after the LAST popup -> next cycle
    fsm.step(EMPTY, t + 0.7 + POPUP_DRAIN_S)
    assert fsm.counters.caught == 1
    assert fsm.state is State.FIND_ZONE


def test_result_without_popup_counts_loss():
    """Escaped fish shows no popup: minigame gone + no popup = loss, restart."""
    fsm = make_fsm()
    t = to_minigame(fsm)
    fsm.step(EMPTY, t + 0.1)  # -> RESULT
    assert fsm.step(EMPTY, t + 0.2) == []  # still waiting for popup
    fsm.step(EMPTY, t + 0.1 + RESULT_WINDOW_S)
    assert fsm.counters.lost == 1
    assert fsm.consecutive_fails == 1
    assert fsm.state is State.FIND_ZONE


def test_result_no_popup_but_bobber_in_water_resumes_wait():
    """Safety: no popup but the rod is still cast -> do NOT recast, wait for bite."""
    fsm = make_fsm()
    t = to_minigame(fsm)
    fsm.step(EMPTY, t + 0.1)  # -> RESULT
    cmds = fsm.step(snap(det(BOBBER_IDLE)), t + 0.1 + RESULT_WINDOW_S)
    assert fsm.state is State.WAIT_BITE
    assert fsm.counters.lost == 0  # not a loss — we are still fishing
    assert not any(isinstance(c, PressLmb) for c in cmds)


# -- stop conditions -------------------------------------------------------------------


def test_five_consecutive_fails_auto_stop_to_idle():
    fsm = make_fsm(max_consecutive_fails=5)
    fsm.start(0.0)
    t = 1.0
    for i in range(5):
        t = fail_one_cycle(fsm, t) + 1.0
        if i < 4:
            assert fsm.state is State.FIND_ZONE
    assert fsm.state is State.IDLE
    assert fsm.consecutive_fails == 5
    assert fsm.counters.lost == 5


def test_session_limit_auto_stop():
    fsm = make_fsm(session_limit=1)
    t = to_minigame(fsm)
    fsm.step(EMPTY, t + 0.1)  # -> RESULT
    fsm.step(snap(det(CATCH_POPUP)), t + 0.2)
    assert fsm.counters.caught == 1
    fsm.step(EMPTY, t + 0.2 + POPUP_DRAIN_S)  # drain window elapses
    assert fsm.state is State.IDLE


def test_stop_releases_held_button():
    fsm = make_fsm()
    t = to_minigame(fsm)
    bar = det(MINIGAME_BAR, bbox=BAR_BBOX)
    zone = det(MINIGAME_ZONE, bbox=ZONE_BBOX)
    float_left = det(MINIGAME_FLOAT, bbox=(150.0, 100.0, 170.0, 130.0))
    fsm.step(snap(bar, zone, float_left), t + 0.1)  # now holding
    cmds = fsm.stop(t + 0.2)
    assert fsm.state is State.IDLE
    assert ReleaseLmb() in cmds
