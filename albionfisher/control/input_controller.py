"""Execute FSM input commands via pydirectinput (DirectInput-compatible).

Coordinates in commands are window-relative; they are translated to screen
coordinates using the target window rect. ``release_all()`` must be called on
any stop path so no button is left held down.
"""

import logging
import time

from albionfisher.capture.window_finder import WindowInfo
from albionfisher.fsm.events import (
    ClickLmb,
    Command,
    HoldLmb,
    MoveTo,
    PressLmb,
    ReleaseLmb,
)

log = logging.getLogger(__name__)


class InputController:
    def __init__(self, window: WindowInfo | None = None) -> None:
        import pydirectinput  # lazy: not needed for unit tests

        pydirectinput.FAILSAFE = False  # corner fail-safe interferes with games
        self._pdi = pydirectinput
        self._window = window
        self._lmb_down = False

    def set_window(self, window: WindowInfo) -> None:
        self._window = window

    def _to_screen(self, x: int, y: int) -> tuple[int, int]:
        if self._window is None:
            return x, y
        left, top, _, _ = self._window.rect
        return left + x, top + y

    # -- command execution ---------------------------------------------------

    def execute(self, command: Command) -> None:
        """Execute one input command. SetFps/Notify belong to the worker."""
        if isinstance(command, MoveTo):
            self.move_to(command.x, command.y)
        elif isinstance(command, PressLmb):
            self.press_lmb(command.duration_ms)
        elif isinstance(command, ClickLmb):
            self.click_lmb()
        elif isinstance(command, HoldLmb):
            self.hold_lmb()
        elif isinstance(command, ReleaseLmb):
            self.release_lmb()

    def move_to(self, x: int, y: int) -> None:
        sx, sy = self._to_screen(x, y)
        self._pdi.moveTo(sx, sy)

    def press_lmb(self, duration_ms: int) -> None:
        """Hold LMB for a fixed duration (cast strength). Blocking."""
        self._pdi.mouseDown(button="left")
        self._lmb_down = True
        time.sleep(duration_ms / 1000.0)
        self._pdi.mouseUp(button="left")
        self._lmb_down = False

    def click_lmb(self) -> None:
        self._pdi.click(button="left")

    def hold_lmb(self) -> None:
        if not self._lmb_down:
            self._pdi.mouseDown(button="left")
            self._lmb_down = True

    def release_lmb(self) -> None:
        if self._lmb_down:
            self._pdi.mouseUp(button="left")
            self._lmb_down = False

    def release_all(self) -> None:
        """Release every held input. Safe to call from any thread, any state."""
        try:
            self._pdi.mouseUp(button="left")
        except Exception:  # pragma: no cover - emergency path must never raise
            log.exception("release_all failed")
        self._lmb_down = False
