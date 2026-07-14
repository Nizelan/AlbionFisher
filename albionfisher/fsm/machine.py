"""FishingFsm: pure transition logic for the fishing cycle (SPEC §5).

Strictly no I/O and no wall-clock — time comes in via the ``now`` parameter
(seconds, monotonic). Each ``step(snapshot, now)`` returns the Commands the
worker must execute. This keeps every transition unit-testable.
"""

from dataclasses import dataclass

from albionfisher.config.settings import Settings
from albionfisher.detection.types import (
    BOBBER_BITE,
    BOBBER_IDLE,
    CATCH_POPUP,
    FISHING_ZONE,
    MINIGAME_BAR,
    MINIGAME_FLOAT,
    MINIGAME_ZONE,
)
from albionfisher.fsm.events import (
    ClickLmb,
    Command,
    DetectionSnapshot,
    HoldLmb,
    MoveTo,
    Notify,
    PressLmb,
    ReleaseLmb,
    SetFps,
)
from albionfisher.fsm.minigame import MinigameAction, decide
from albionfisher.fsm.states import State

MAX_CAST_ATTEMPTS = 3  # SPEC §5: repeat CAST at most 3 times
RESULT_WINDOW_S = 2.0  # how long RESULT waits for catch_popup before counting a loss
# After the first popup, keep absorbing follow-up popups (e.g. seaweed caught
# together with the fish shows a second popup) until none are seen for this long.
POPUP_DRAIN_S = 1.0


@dataclass
class FsmCounters:
    caught: int = 0
    lost: int = 0
    recasts: int = 0


class FishingFsm:
    def __init__(self, settings: Settings) -> None:
        self._cfg = settings
        self.state = State.IDLE
        self.counters = FsmCounters()
        self.consecutive_fails = 0
        self._entered_at = 0.0
        self._cast_target: tuple[float, float] | None = None
        self._cast_attempts = 0
        self._holding = False
        self._result_failed = False  # minigame reported the fish escaped
        self._caught_this_result = False  # popup already counted for this cycle
        self._last_popup_at: float | None = None

    # -- public API ---------------------------------------------------------

    def time_in_state(self, now: float) -> float:
        return now - self._entered_at

    def start(self, now: float) -> list[Command]:
        """Start button pressed: IDLE -> FIND_ZONE."""
        if self.state is not State.IDLE:
            return []
        self.consecutive_fails = 0
        return self._enter(State.FIND_ZONE, now)

    def stop(self, now: float) -> list[Command]:
        """Stop from any state: release everything, go IDLE."""
        cmds: list[Command] = []
        if self._holding:
            self._holding = False
            cmds.append(ReleaseLmb())
        cmds += self._enter(State.IDLE, now)
        return cmds

    def step(self, snapshot: DetectionSnapshot, now: float) -> list[Command]:
        handlers = {
            State.IDLE: self._step_idle,
            State.FIND_ZONE: self._step_find_zone,
            State.CAST: self._step_cast,
            State.WAIT_BITE: self._step_wait_bite,
            State.HOOK: self._step_hook,
            State.MINIGAME: self._step_minigame,
            State.RESULT: self._step_result,
        }
        return handlers[self.state](snapshot, now)

    # -- transitions --------------------------------------------------------

    def _enter(self, state: State, now: float) -> list[Command]:
        previous = self.state
        self.state = state
        self._entered_at = now
        cmds: list[Command] = []

        if previous is State.MINIGAME and state is not State.MINIGAME:
            if self._holding:
                self._holding = False
                cmds.append(ReleaseLmb())
            cmds.append(SetFps(self._cfg.detection.idle_fps))

        if state is State.CAST:
            self._cast_attempts += 1
            if self._cast_target is not None:
                x, y = self._cast_target
                cmds.append(MoveTo(int(x), int(y)))
            cmds.append(PressLmb(self._cfg.cast.hold_ms))
        elif state is State.HOOK:
            cmds.append(ClickLmb())
        elif state is State.MINIGAME:
            cmds.append(SetFps(self._cfg.detection.minigame_fps))
        elif state is State.RESULT:
            self._caught_this_result = False
            self._last_popup_at = None
        return cmds

    def _register_fail(self, now: float, reason: str) -> list[Command]:
        """Common fail path: count it, auto-stop after too many in a row."""
        self.counters.lost += 1
        self.consecutive_fails += 1
        cmds: list[Command] = [Notify(f"fail: {reason}")]
        cmds += self._after_result(now)
        return cmds

    def _after_result(self, now: float) -> list[Command]:
        """Decide where to go after an outcome: next cycle or auto-stop."""
        stop_cfg = self._cfg.stop
        if self.consecutive_fails >= stop_cfg.max_consecutive_fails:
            cmds: list[Command] = [
                Notify(f"auto-stop: {self.consecutive_fails} consecutive fails")
            ]
            cmds += self._enter(State.IDLE, now)
            return cmds
        if (
            stop_cfg.session_limit is not None
            and self.counters.caught >= stop_cfg.session_limit
        ):
            cmds = [Notify(f"auto-stop: session limit {stop_cfg.session_limit} reached")]
            cmds += self._enter(State.IDLE, now)
            return cmds
        return self._enter(State.FIND_ZONE, now)

    # -- per-state steps ----------------------------------------------------

    def _step_idle(self, snapshot: DetectionSnapshot, now: float) -> list[Command]:
        return []

    def _step_find_zone(self, snapshot: DetectionSnapshot, now: float) -> list[Command]:
        # Safety guard: never cast while the bobber is already in the water —
        # a cast press would retract the rod before the bite. Resume waiting.
        if snapshot.best(BOBBER_IDLE) is not None:
            cmds: list[Command] = [Notify("bobber already in water, resuming wait for bite")]
            cmds += self._enter(State.WAIT_BITE, now)
            return cmds
        zone = snapshot.best(FISHING_ZONE)
        if zone is not None:
            self._cast_target = zone.center
            self._cast_attempts = 0
            return self._enter(State.CAST, now)
        if self.time_in_state(now) >= self._cfg.timeouts.find_zone:
            self._entered_at = now  # pause + retry, keep looking
            return [Notify("fishing_zone not found, retrying")]
        return []

    def _step_cast(self, snapshot: DetectionSnapshot, now: float) -> list[Command]:
        if snapshot.best(BOBBER_IDLE) is not None:
            return self._enter(State.WAIT_BITE, now)
        if self.time_in_state(now) >= self._cfg.timeouts.cast_confirm:
            if self._cast_attempts >= MAX_CAST_ATTEMPTS:
                return self._register_fail(
                    now, f"bobber did not appear after {self._cast_attempts} casts"
                )
            cmds: list[Command] = [Notify("cast not confirmed, retrying")]
            cmds += self._enter(State.CAST, now)
            return cmds
        return []

    def _step_wait_bite(self, snapshot: DetectionSnapshot, now: float) -> list[Command]:
        if snapshot.best(BOBBER_BITE) is not None:
            return self._enter(State.HOOK, now)
        if self.time_in_state(now) >= self._cfg.timeouts.bite:
            self.counters.recasts += 1
            self._cast_attempts = 0
            cmds: list[Command] = [Notify("bite timeout, recasting")]
            cmds += self._enter(State.CAST, now)
            return cmds
        return []

    def _step_hook(self, snapshot: DetectionSnapshot, now: float) -> list[Command]:
        if snapshot.best(MINIGAME_BAR) is not None:
            return self._enter(State.MINIGAME, now)
        if self.time_in_state(now) >= self._cfg.timeouts.minigame_start:
            self._result_failed = False  # empty hook: RESULT decides via popup
            cmds: list[Command] = [Notify("minigame did not start")]
            cmds += self._enter(State.RESULT, now)
            return cmds
        return []

    def _step_minigame(self, snapshot: DetectionSnapshot, now: float) -> list[Command]:
        bar = snapshot.best(MINIGAME_BAR)
        if bar is None:
            self._result_failed = False  # bar gone: outcome resolved via popup
            return self._enter(State.RESULT, now)

        float_det = snapshot.best(MINIGAME_FLOAT)
        zone_det = snapshot.best(MINIGAME_ZONE)

        # Float escaped past the bar boundaries -> the fish broke free.
        if float_det is not None:
            fx, _ = float_det.center
            if fx < bar.bbox[0] or fx > bar.bbox[2]:
                self._result_failed = True
                cmds: list[Command] = [Notify("float escaped the bar, fish lost")]
                cmds += self._enter(State.RESULT, now)
                return cmds

        cmds = []
        if zone_det is None or float_det is None:
            cmds.append(Notify("minigame zone/float not detected"))
        action = decide(
            float_det.bbox if float_det else None,
            zone_det.bbox if zone_det else None,
            self._cfg.minigame,
            self._holding,
        )
        if action is MinigameAction.HOLD and not self._holding:
            self._holding = True
            cmds.append(HoldLmb())
        elif action is MinigameAction.RELEASE and self._holding:
            self._holding = False
            cmds.append(ReleaseLmb())
        return cmds

    def _step_result(self, snapshot: DetectionSnapshot, now: float) -> list[Command]:
        if self._result_failed:
            self._result_failed = False
            return self._register_fail(now, "fish escaped in minigame")

        if snapshot.best(CATCH_POPUP) is not None:
            # A catch can produce several popups (e.g. seaweed pulled out with
            # the fish). Count the catch once and keep draining popups so the
            # next cycle does not misread a leftover popup.
            self._last_popup_at = now
            if not self._caught_this_result:
                self._caught_this_result = True
                self.counters.caught += 1
                self.consecutive_fails = 0
                return [Notify("fish caught")]
            return []

        if self._caught_this_result:
            if self._last_popup_at is not None and now - self._last_popup_at >= POPUP_DRAIN_S:
                return self._after_result(now)
            return []  # brief gap between popups — keep draining

        if self.time_in_state(now) >= RESULT_WINDOW_S:
            # No popup at all: the fish escaped (escapes show no popup) — but
            # only restart if we are not actually still fishing. If the bobber
            # is visible the rod is still cast; recasting would retract it.
            if snapshot.best(BOBBER_IDLE) is not None:
                cmds: list[Command] = [
                    Notify("no popup but bobber still in water, resuming wait")
                ]
                cmds += self._enter(State.WAIT_BITE, now)
                return cmds
            return self._register_fail(now, "no catch popup, fish escaped")
        return []
