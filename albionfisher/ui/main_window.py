"""Main window: window picker, Start/Stop, status, counters, settings, log."""

import logging

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from albionfisher import __version__
from albionfisher.capture.window_finder import WindowInfo, list_game_windows
from albionfisher.config.settings import Settings
from albionfisher.control.emergency import (
    DEFAULT_HOTKEY,
    install_kill_switch,
    remove_kill_switch,
)
from albionfisher.ui.log_handler import QtLogHandler
from albionfisher.ui.worker import BotWorker

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings, qt_log_handler: QtLogHandler) -> None:
        super().__init__()
        self._settings = settings
        self._worker: BotWorker | None = None
        self._kill_switch_handle: object | None = None
        self._windows: list[WindowInfo] = []

        self.setWindowTitle(f"AlbionFisher v{__version__}")
        self.resize(760, 640)
        self._build_ui()

        qt_log_handler.message.connect(self._append_log)
        self._refresh_windows()

        self._session_timer = QTimer(self)
        self._session_timer.setInterval(1000)
        self._session_timer.timeout.connect(self._tick_session_time)
        self._session_seconds = 0

    # -- UI construction -----------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)

        self._banner = QLabel("")
        self._banner.setWordWrap(True)
        self._banner.setStyleSheet(
            "background: #7a4a00; color: white; padding: 6px; border-radius: 4px;"
        )
        self._banner.hide()
        root.addWidget(self._banner)

        window_row = QHBoxLayout()
        window_row.addWidget(QLabel("Game window:"))
        self._window_combo = QComboBox()
        self._window_combo.setMinimumWidth(320)
        window_row.addWidget(self._window_combo, stretch=1)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_windows)
        window_row.addWidget(refresh_btn)
        root.addLayout(window_row)

        controls_row = QHBoxLayout()
        self._start_btn = QPushButton("Start")
        self._start_btn.clicked.connect(self._on_start)
        self._stop_btn = QPushButton("Stop")
        self._stop_btn.clicked.connect(self._on_stop)
        self._stop_btn.setEnabled(False)
        controls_row.addWidget(self._start_btn)
        controls_row.addWidget(self._stop_btn)
        controls_row.addWidget(QLabel(f"Emergency stop: {DEFAULT_HOTKEY.upper()} (global)"))
        controls_row.addStretch(1)
        root.addLayout(controls_row)

        status_box = QGroupBox("Status")
        status_grid = QGridLayout(status_box)
        self._state_label = QLabel("IDLE")
        self._state_time_label = QLabel("0.0 s")
        self._fps_label = QLabel("—")
        self._session_label = QLabel("00:00:00")
        status_grid.addWidget(QLabel("FSM state:"), 0, 0)
        status_grid.addWidget(self._state_label, 0, 1)
        status_grid.addWidget(QLabel("Time in state:"), 0, 2)
        status_grid.addWidget(self._state_time_label, 0, 3)
        status_grid.addWidget(QLabel("Detection FPS:"), 1, 0)
        status_grid.addWidget(self._fps_label, 1, 1)
        status_grid.addWidget(QLabel("Session time:"), 1, 2)
        status_grid.addWidget(self._session_label, 1, 3)
        root.addWidget(status_box)

        counters_box = QGroupBox("Counters")
        counters_grid = QGridLayout(counters_box)
        self._caught_label = QLabel("0")
        self._lost_label = QLabel("0")
        self._recasts_label = QLabel("0")
        counters_grid.addWidget(QLabel("Caught:"), 0, 0)
        counters_grid.addWidget(self._caught_label, 0, 1)
        counters_grid.addWidget(QLabel("Lost:"), 0, 2)
        counters_grid.addWidget(self._lost_label, 0, 3)
        counters_grid.addWidget(QLabel("Recasts:"), 0, 4)
        counters_grid.addWidget(self._recasts_label, 0, 5)
        root.addWidget(counters_box)

        settings_box = QGroupBox("Settings")
        form = QFormLayout(settings_box)
        self._model_path_edit = QLineEdit(self._settings.detection.model_path)
        form.addRow("Model path:", self._model_path_edit)
        self._conf_spin = QDoubleSpinBox()
        self._conf_spin.setRange(0.05, 1.0)
        self._conf_spin.setSingleStep(0.05)
        self._conf_spin.setValue(self._settings.detection.conf_threshold)
        form.addRow("Confidence threshold:", self._conf_spin)
        self._bite_timeout_spin = QSpinBox()
        self._bite_timeout_spin.setRange(5, 300)
        self._bite_timeout_spin.setValue(int(self._settings.timeouts.bite))
        form.addRow("Bite timeout (s):", self._bite_timeout_spin)
        self._cast_hold_spin = QSpinBox()
        self._cast_hold_spin.setRange(50, 5000)
        self._cast_hold_spin.setValue(self._settings.cast.hold_ms)
        form.addRow("Cast hold (ms):", self._cast_hold_spin)
        self._max_fails_spin = QSpinBox()
        self._max_fails_spin.setRange(1, 50)
        self._max_fails_spin.setValue(self._settings.stop.max_consecutive_fails)
        form.addRow("Max consecutive fails:", self._max_fails_spin)
        root.addWidget(settings_box)

        self._log_view = QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumBlockCount(2000)
        root.addWidget(self._log_view, stretch=1)

        self.setCentralWidget(central)

    # -- slots ----------------------------------------------------------------

    def _refresh_windows(self) -> None:
        try:
            self._windows = list_game_windows()
        except Exception as exc:
            log.error("window enumeration failed: %s", exc)
            self._windows = []
        self._window_combo.clear()
        for window in self._windows:
            self._window_combo.addItem(f"{window.title}  [{window.hwnd}]")
        if not self._windows:
            self._window_combo.addItem("— no Albion Online window found —")
        log.info("window list refreshed: %d match(es)", len(self._windows))

    def _apply_ui_settings(self) -> None:
        d = self._settings.detection
        d.model_path = self._model_path_edit.text().strip()
        d.conf_threshold = self._conf_spin.value()
        self._settings.timeouts.bite = float(self._bite_timeout_spin.value())
        self._settings.cast.hold_ms = self._cast_hold_spin.value()
        self._settings.stop.max_consecutive_fails = self._max_fails_spin.value()

    def _on_start(self) -> None:
        index = self._window_combo.currentIndex()
        if not self._windows or index < 0 or index >= len(self._windows):
            log.error("select a game window first (press Refresh)")
            return
        self._apply_ui_settings()

        worker = BotWorker(self._settings, self._windows[index])
        worker.state_changed.connect(self._on_state_changed)
        worker.counters_changed.connect(self._on_counters_changed)
        worker.fps_changed.connect(lambda fps: self._fps_label.setText(f"{fps:.1f}"))
        worker.detector_status_changed.connect(self._on_detector_status)
        worker.error.connect(lambda msg: log.error("%s", msg))
        worker.finished.connect(self._on_worker_finished)

        self._kill_switch_handle = install_kill_switch(
            worker.stop_event,
            release_all=lambda: worker.controller.release_all()
            if worker.controller
            else None,
        )

        self._worker = worker
        self._session_seconds = 0
        self._session_timer.start()
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        log.info("session started on window '%s'", self._windows[index].title)
        worker.start()

    def _on_stop(self) -> None:
        if self._worker is not None:
            log.info("stop requested")
            self._worker.request_stop()

    def _on_worker_finished(self) -> None:
        if self._kill_switch_handle is not None:
            remove_kill_switch(self._kill_switch_handle)
            self._kill_switch_handle = None
        self._worker = None
        self._session_timer.stop()
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._state_label.setText("IDLE")
        log.info("session finished")

    def _on_state_changed(self, state: str, seconds: float) -> None:
        self._state_label.setText(state)
        self._state_time_label.setText(f"{seconds:.1f} s")

    def _on_counters_changed(self, caught: int, lost: int, recasts: int) -> None:
        self._caught_label.setText(str(caught))
        self._lost_label.setText(str(lost))
        self._recasts_label.setText(str(recasts))

    def _on_detector_status(self, ok: bool, message: str) -> None:
        if ok:
            self._banner.hide()
            log.info("detector: %s", message)
        else:
            self._banner.setText(f"Detector degraded: {message}")
            self._banner.show()
            log.warning("detector: %s", message)

    def _tick_session_time(self) -> None:
        self._session_seconds += 1
        hours, rem = divmod(self._session_seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        self._session_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def _append_log(self, line: str) -> None:
        self._log_view.appendPlainText(line)

    # -- lifecycle -------------------------------------------------------------

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        if self._worker is not None:
            self._worker.request_stop()
            self._worker.wait(3000)
        if self._kill_switch_handle is not None:
            remove_kill_switch(self._kill_switch_handle)
        super().closeEvent(event)
