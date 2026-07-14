"""Frame sources: dxcam (fast, preferred) with mss fallback.

``grab()`` returns a BGR ``np.ndarray`` of the window client region, or ``None``
when the window is lost/minimized — the worker must pause in that case.
"""

import logging
from typing import TYPE_CHECKING, Protocol

from albionfisher.capture.window_finder import WindowInfo, is_minimized, refresh_rect

if TYPE_CHECKING:
    import numpy as np

log = logging.getLogger(__name__)


class FrameSource(Protocol):
    def start(self, window: WindowInfo) -> None: ...

    def grab(self) -> "np.ndarray | None": ...

    def stop(self) -> None: ...


class DxcamSource:
    """Desktop-duplication capture via dxcam. Fast enough for the minigame."""

    def __init__(self) -> None:
        self._camera = None
        self._window: WindowInfo | None = None

    def start(self, window: WindowInfo) -> None:
        import dxcam  # lazy heavy import

        self._window = window
        self._camera = dxcam.create(output_color="BGR")
        if self._camera is None:
            raise RuntimeError("dxcam.create() returned None (no capture device)")

    def grab(self) -> "np.ndarray | None":
        if self._camera is None or self._window is None:
            return None
        window = refresh_rect(self._window)
        if window is None or is_minimized(window):
            return None
        self._window = window
        frame = self._camera.grab(region=window.rect)
        return frame  # dxcam returns None when the screen content is unchanged

    def stop(self) -> None:
        if self._camera is not None:
            try:
                self._camera.release()
            except Exception:  # pragma: no cover - best-effort cleanup
                pass
        self._camera = None
        self._window = None


class MssSource:
    """Portable GDI-based capture via mss. Slower but always available."""

    def __init__(self) -> None:
        self._sct = None
        self._window: WindowInfo | None = None

    def start(self, window: WindowInfo) -> None:
        import mss  # lazy

        self._window = window
        self._sct = mss.mss()

    def grab(self) -> "np.ndarray | None":
        import numpy as np  # lazy

        if self._sct is None or self._window is None:
            return None
        window = refresh_rect(self._window)
        if window is None or is_minimized(window):
            return None
        self._window = window
        left, top, right, bottom = window.rect
        raw = self._sct.grab(
            {"left": left, "top": top, "width": right - left, "height": bottom - top}
        )
        frame = np.asarray(raw)[:, :, :3]  # BGRA -> BGR
        return np.ascontiguousarray(frame)

    def stop(self) -> None:
        if self._sct is not None:
            try:
                self._sct.close()
            except Exception:  # pragma: no cover - best-effort cleanup
                pass
        self._sct = None
        self._window = None


def create_frame_source() -> FrameSource:
    """Prefer dxcam; fall back to mss with a logged warning."""
    try:
        import dxcam  # noqa: F401  lazy availability probe

        return DxcamSource()
    except Exception as exc:
        log.warning("dxcam unavailable (%s); falling back to mss capture", exc)
        return MssSource()
