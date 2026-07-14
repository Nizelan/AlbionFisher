"""BotWorker: the capture -> detect -> FSM -> control loop on a QThread.

The worker owns all runtime objects (frame source, detector, FSM, input
controller). Communication: worker -> UI via Qt signals only; UI -> worker via
a threading.Event (stop). The loop is sequential, throttled to the FSM-chosen
target FPS (idle vs minigame).
"""

import logging
import threading
import time

from PySide6.QtCore import QThread, Signal

from albionfisher.capture.frame_source import create_frame_source
from albionfisher.capture.window_finder import WindowInfo
from albionfisher.config.settings import Settings
from albionfisher.control.input_controller import InputController
from albionfisher.detection.detector import create_detector
from albionfisher.fsm.events import DetectionSnapshot, Notify, SetFps
from albionfisher.fsm.machine import FishingFsm
from albionfisher.fsm.states import State

log = logging.getLogger(__name__)

WINDOW_LOST_PAUSE_S = 1.0


class BotWorker(QThread):
    state_changed = Signal(str, float)  # state name, time in state (s)
    counters_changed = Signal(int, int, int)  # caught, lost, recasts
    fps_changed = Signal(float)
    detector_status_changed = Signal(bool, str)
    error = Signal(str)

    def __init__(self, settings: Settings, window: WindowInfo) -> None:
        super().__init__()
        self._settings = settings
        self._window = window
        self.stop_event = threading.Event()
        self.controller: InputController | None = None

    def request_stop(self) -> None:
        self.stop_event.set()

    # NEEDS-MODEL: the full loop can only be exercised end-to-end with trained
    # weights and a running game; unit tests cover the pure FSM instead.
    def run(self) -> None:  # pragma: no cover - thread + hardware bound
        source = None
        try:
            self.controller = InputController(self._window)
            detector = create_detector(
                self._settings.detection.model_path,
                self._settings.detection.conf_threshold,
            )
            status = detector.status
            self.detector_status_changed.emit(status.ok, status.message)

            source = create_frame_source()
            source.start(self._window)

            fsm = FishingFsm(self._settings)
            target_fps = self._settings.detection.idle_fps

            for command in fsm.start(time.monotonic()):
                target_fps = self._dispatch(command, target_fps)

            last_frame = None
            while not self.stop_event.is_set():
                tick_start = time.monotonic()

                frame = source.grab()
                if frame is None:
                    frame = last_frame  # dxcam returns None on unchanged screens
                if frame is None:
                    self.error.emit("game window lost/minimized — paused")
                    self.controller.release_all()
                    if self.stop_event.wait(WINDOW_LOST_PAUSE_S):
                        break
                    continue
                last_frame = frame

                detections = tuple(detector.infer(frame))
                snapshot = DetectionSnapshot(detections=detections)

                now = time.monotonic()
                for command in fsm.step(snapshot, now):
                    target_fps = self._dispatch(command, target_fps)

                self.state_changed.emit(fsm.state.value, fsm.time_in_state(now))
                counters = fsm.counters
                self.counters_changed.emit(
                    counters.caught, counters.lost, counters.recasts
                )

                if fsm.state is State.IDLE:
                    log.info("FSM reached IDLE (auto-stop) — worker finishing")
                    break

                elapsed = time.monotonic() - tick_start
                self.fps_changed.emit(1.0 / elapsed if elapsed > 0 else float(target_fps))
                budget = 1.0 / target_fps
                if elapsed < budget and self.stop_event.wait(budget - elapsed):
                    break
        except Exception as exc:
            log.exception("worker crashed")
            self.error.emit(f"worker crashed: {exc}")
        finally:
            if self.controller is not None:
                self.controller.release_all()
            if source is not None:
                source.stop()
            log.info("worker stopped")

    def _dispatch(self, command, target_fps: int) -> int:
        """Execute one FSM command; returns the (possibly updated) target FPS."""
        if isinstance(command, SetFps):
            return command.fps
        if isinstance(command, Notify):
            log.info(command.event)
            return target_fps
        assert self.controller is not None
        self.controller.execute(command)
        return target_fps
