"""System overview dashboard with stat cards."""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..models.snapshot import Snapshot
from ..utils.helpers import format_bytes, format_duration


class StatCard(QFrame):
    def __init__(self, title: str, value: str = "--", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setStyleSheet("""
            StatCard {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #a6adc8; font-size: 11px; border: none;")

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            "color: #cdd6f4; font-size: 20px; font-weight: bold; border: none;"
        )

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str):
        self.value_label.setText(value)


class Dashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.cpu_card = StatCard("CPU 使用率")
        self.mem_card = StatCard("内存")
        self.proc_card = StatCard("进程数")
        self.thread_card = StatCard("线程数")
        self.handle_card = StatCard("句柄数")
        self.uptime_card = StatCard("系统运行时间")

        layout.addWidget(self.cpu_card, 0, 0)
        layout.addWidget(self.mem_card, 0, 1)
        layout.addWidget(self.proc_card, 1, 0)
        layout.addWidget(self.thread_card, 1, 1)
        layout.addWidget(self.handle_card, 2, 0)
        layout.addWidget(self.uptime_card, 2, 1)

    def update_from_snapshot(self, snapshot: Snapshot):
        sys = snapshot.system
        self.cpu_card.set_value(f"{sys.cpu_percent:.1f}%")
        self.mem_card.set_value(
            f"{sys.memory_percent:.1f}%  ({format_bytes(sys.memory_total - sys.memory_available)} / {format_bytes(sys.memory_total)})"
        )
        self.proc_card.set_value(str(sys.total_processes))
        self.thread_card.set_value(str(sys.total_threads))
        self.handle_card.set_value(str(sys.total_handles))
        self.uptime_card.set_value(format_duration(
            __import__("datetime").timedelta(seconds=sys.uptime_seconds)
        ))
