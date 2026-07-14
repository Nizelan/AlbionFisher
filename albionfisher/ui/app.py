"""Application bootstrap: settings + logging + Qt main window."""

import logging
import sys
from pathlib import Path

USER_SETTINGS_PATH = Path("config") / "settings.yaml"

log = logging.getLogger(__name__)


def main() -> int:
    from PySide6.QtWidgets import QApplication, QMessageBox  # lazy heavy import

    from albionfisher.config.settings import SettingsError, load_settings
    from albionfisher.ui.log_handler import setup_logging
    from albionfisher.ui.main_window import MainWindow

    app = QApplication(sys.argv)

    qt_handler, log_file = setup_logging()
    logging.getLogger(__name__).info("logging to %s", log_file)

    try:
        settings = load_settings(USER_SETTINGS_PATH)
    except SettingsError as exc:
        QMessageBox.critical(None, "AlbionFisher", f"Invalid settings:\n{exc}")
        return 2

    window = MainWindow(settings, qt_handler)
    window.show()
    return app.exec()
