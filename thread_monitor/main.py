"""Thread Monitor - Windows process and thread monitoring tool.

Usage: python -m thread_monitor.main
"""

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from .views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Thread Monitor")
    app.setOrganizationName("ThreadMonitor")

    # Enable high-DPI scaling
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
