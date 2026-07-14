"""Enumerate top-level windows and find the Albion Online game window."""

from dataclasses import dataclass

DEFAULT_TITLE_FILTER = "Albion Online"


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    title: str
    rect: tuple[int, int, int, int]  # screen coords: left, top, right, bottom

    @property
    def width(self) -> int:
        return self.rect[2] - self.rect[0]

    @property
    def height(self) -> int:
        return self.rect[3] - self.rect[1]


def list_game_windows(title_filter: str = DEFAULT_TITLE_FILTER) -> list[WindowInfo]:
    """List visible top-level windows whose title contains *title_filter*.

    Pass an empty filter to list all visible titled windows.
    """
    import win32gui  # lazy: pywin32 not needed for unit tests

    windows: list[WindowInfo] = []

    def _on_window(hwnd: int, _arg: object) -> None:
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return
        if title_filter.lower() not in title.lower():
            return
        rect = win32gui.GetWindowRect(hwnd)
        windows.append(WindowInfo(hwnd=hwnd, title=title, rect=rect))

    win32gui.EnumWindows(_on_window, None)
    return windows


def refresh_rect(window: WindowInfo) -> "WindowInfo | None":
    """Re-read the window rect; returns None if the window no longer exists."""
    import win32gui  # lazy

    if not win32gui.IsWindow(window.hwnd) or not win32gui.IsWindowVisible(window.hwnd):
        return None
    rect = win32gui.GetWindowRect(window.hwnd)
    return WindowInfo(hwnd=window.hwnd, title=window.title, rect=rect)


def is_minimized(window: WindowInfo) -> bool:
    import win32gui  # lazy

    return bool(win32gui.IsIconic(window.hwnd))
