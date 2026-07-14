"""Global emergency kill switch (SPEC §6/§8: stop from any state in <=200 ms).

The `keyboard` library invokes the callback on its own listener thread, so the
stop event is set and inputs are released immediately — without waiting for
the worker loop to notice.
"""

import logging
import threading
from collections.abc import Callable

log = logging.getLogger(__name__)

DEFAULT_HOTKEY = "f10"


def install_kill_switch(
    stop_event: threading.Event,
    release_all: Callable[[], None] | None = None,
    hotkey: str = DEFAULT_HOTKEY,
) -> object:
    """Register a global hotkey; returns a handle for remove_kill_switch."""
    import keyboard  # lazy: not needed for unit tests

    def _trigger() -> None:
        log.warning("emergency stop (%s) pressed", hotkey.upper())
        stop_event.set()
        if release_all is not None:
            try:
                release_all()
            except Exception:  # pragma: no cover - emergency path must never raise
                log.exception("release_all failed in kill switch")

    return keyboard.add_hotkey(hotkey, _trigger)


def remove_kill_switch(handle: object) -> None:
    import keyboard  # lazy

    try:
        keyboard.remove_hotkey(handle)
    except (KeyError, ValueError):
        pass
