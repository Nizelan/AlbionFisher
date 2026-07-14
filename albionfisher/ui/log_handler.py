"""Logging plumbing: file log + Qt-signal handler for the UI log widget."""

import logging
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal

LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


class QtLogHandler(logging.Handler, QObject):
    """Forwards log records to the UI thread via a Qt signal."""

    message = Signal(str)

    def __init__(self) -> None:
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.setFormatter(logging.Formatter("%(asctime)s  %(message)s", "%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.message.emit(self.format(record))
        except Exception:  # pragma: no cover - logging must never raise
            self.handleError(record)


def setup_logging(log_dir: "str | Path" = "logs") -> tuple[QtLogHandler, Path]:
    """Configure root logging: session file + Qt handler. Returns (handler, file)."""
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"session_{datetime.now():%Y%m%d_%H%M%S}.log"

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(file_handler)

    qt_handler = QtLogHandler()
    root.addHandler(qt_handler)
    return qt_handler, log_file
