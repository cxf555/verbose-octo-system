"""Thread list table view for the selected process."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableView, QHeaderView,
)
from PySide6.QtCore import Qt, QAbstractTableModel, Signal, QModelIndex
from PySide6.QtGui import QColor

from ..models.process_info import ProcessInfo, ThreadInfo
from ..utils.win32_constants import THREAD_PRIORITY_NAMES, IO_PRIORITY_NAMES, PAGE_PRIORITY_NAMES
from ..utils.helpers import format_number, format_hex


class ThreadTableModel(QAbstractTableModel):
    COLUMNS = [
        ("TID", "tid"),
        ("用户CPU", "cpu_user_time"),
        ("内核CPU", "cpu_kernel_time"),
        ("基础优先级", "base_priority"),
        ("动态优先级", "dynamic_priority"),
        ("IO优先级", "io_priority"),
        ("页面优先级", "page_priority"),
        ("上下文切换", "context_switches"),
        ("起始地址", "start_address"),
        ("亲和性", "affinity_mask"),
        ("状态", "thread_state"),
        ("等待原因", "wait_reason"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._threads: list[ThreadInfo] = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._threads)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNS)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section][0]
        return None

    def data(self, index, role):
        if not index.isValid():
            return None
        t = self._threads[index.row()]
        col_key = self.COLUMNS[index.column()][1]

        if role == Qt.DisplayRole:
            val = getattr(t, col_key, "")
            if col_key == "tid":
                return str(val)
            if col_key == "cpu_user_time":
                return str(val.time().strftime("%H:%M:%S")) if val else ""
            if col_key == "cpu_kernel_time":
                return str(val.time().strftime("%H:%M:%S")) if val else ""
            if col_key == "base_priority":
                return THREAD_PRIORITY_NAMES.get(val, str(val))
            if col_key == "io_priority":
                return IO_PRIORITY_NAMES.get(val, str(val)) if val is not None else ""
            if col_key == "page_priority":
                return PAGE_PRIORITY_NAMES.get(val, str(val)) if val is not None else ""
            if col_key == "context_switches":
                return format_number(val)
            if col_key == "start_address":
                return format_hex(val, 64) if val else ""
            if col_key == "affinity_mask":
                return format_hex(val, 64) if val else ""
            return str(val) if val is not None else ""

        if role == Qt.TextAlignmentRole:
            if col_key in ("tid", "context_switches"):
                return Qt.AlignRight | Qt.AlignVCenter

        if role == Qt.ForegroundRole:
            if t.is_suspicious:
                return QColor("#f38ba8")

        if role == Qt.UserRole:
            return t

        return None

    def set_threads(self, threads: list[ThreadInfo]):
        self.beginResetModel()
        self._threads = sorted(threads, key=lambda t: t.tid)
        self.endResetModel()

    def get_thread(self, row: int) -> ThreadInfo | None:
        if 0 <= row < len(self._threads):
            return self._threads[row]
        return None


class ThreadTableView(QWidget):
    thread_selected = Signal(ThreadInfo)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel("线程")
        self.title_label.setStyleSheet("font-weight: bold; padding: 4px;")

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 70)   # TID
        self.table.setColumnWidth(1, 100)  # 用户CPU
        self.table.setColumnWidth(2, 100)  # 内核CPU
        self.table.setColumnWidth(3, 90)   # 基础优先级
        self.table.setColumnWidth(4, 90)   # 动态优先级
        self.table.setColumnWidth(5, 80)   # IO优先级
        self.table.setColumnWidth(6, 90)   # 页面优先级
        self.table.setColumnWidth(7, 110)  # 上下文切换
        self.table.setColumnWidth(8, 140)  # 起始地址
        self.table.setColumnWidth(9, 140)  # 亲和性
        self.table.setColumnWidth(10, 80)  # 状态
        self.table.setColumnWidth(11, 180) # 等待原因

        layout.addWidget(self.title_label)
        layout.addWidget(self.table)

        self._model = ThreadTableModel()
        self.table.setModel(self._model)

        self.table.selectionModel().selectionChanged.connect(self._on_selection)

    def _on_selection(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return
        t = self._model.get_thread(indexes[0].row())
        if t:
            self.thread_selected.emit(t)

    def show_threads_for_process(self, proc: ProcessInfo):
        self.title_label.setText(f"线程 ({len(proc.threads)}) - {proc.name}")
        self._model.set_threads(proc.threads)

    def clear(self):
        self.title_label.setText("线程")
        self._model.set_threads([])
