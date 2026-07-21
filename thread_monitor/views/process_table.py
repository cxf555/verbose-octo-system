"""Process list table view with sorting and filtering."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QTableView, QHeaderView,
)
from PySide6.QtCore import (
    Qt, QAbstractTableModel, QSortFilterProxyModel, Signal, QModelIndex,
)
from PySide6.QtGui import QColor

from ..models.snapshot import Snapshot
from ..models.process_info import ProcessInfo
from ..utils.helpers import format_bytes, format_duration, format_number


class ProcessTableModel(QAbstractTableModel):
    COLUMNS = [
        ("PID", "pid"),
        ("进程名", "name"),
        ("父PID", "parent_pid"),
        ("CPU %", "cpu_percent"),
        ("工作集", "memory_working_set"),
        ("私有内存", "memory_private_bytes"),
        ("虚拟内存", "memory_virtual_size"),
        ("线程数", "thread_count"),
        ("句柄数", "handle_count"),
        ("运行时长", "running_time"),
        ("命令行", "command_line"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._processes: list[ProcessInfo] = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._processes)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNS)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section][0]
        return None

    def data(self, index, role):
        if not index.isValid():
            return None
        proc = self._processes[index.row()]
        col_key = self.COLUMNS[index.column()][1]

        if role == Qt.DisplayRole:
            val = getattr(proc, col_key, "")
            if col_key == "memory_working_set":
                return format_bytes(val) if val else "0 B"
            if col_key == "memory_private_bytes":
                return format_bytes(val) if val else "0 B"
            if col_key == "memory_virtual_size":
                return format_bytes(val) if val else "0 B"
            if col_key == "cpu_percent":
                return f"{val:.1f}" if val else "0.0"
            if col_key == "running_time":
                return format_duration(val) if val else ""
            if col_key == "handle_count":
                return format_number(val) if val else "0"
            return str(val) if val is not None else ""

        if role == Qt.TextAlignmentRole:
            if col_key in ("pid", "parent_pid", "thread_count", "handle_count"):
                return Qt.AlignRight | Qt.AlignVCenter

        if role == Qt.ForegroundRole:
            if col_key == "name" and proc.is_suspicious:
                return QColor("#f38ba8")
            if col_key == "cpu_percent" and proc.cpu_percent > 50:
                return QColor("#fab387")

        if role == Qt.UserRole:
            return proc

        return None

    def update_processes(self, processes: list[ProcessInfo]):
        self.beginResetModel()
        self._processes = sorted(processes, key=lambda p: p.pid)
        self.endResetModel()

    def get_process(self, row: int) -> ProcessInfo | None:
        if 0 <= row < len(self._processes):
            return self._processes[row]
        return None

    def get_process_by_pid(self, pid: int) -> ProcessInfo | None:
        for p in self._processes:
            if p.pid == pid:
                return p
        return None


class ProcessFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_text = ""

    def set_filter(self, text: str):
        self._filter_text = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self._filter_text:
            return True
        model = self.sourceModel()
        proc = model.get_process(source_row)
        if not proc:
            return True
        searchable = f"{proc.pid} {proc.name.lower()} {proc.command_line.lower()}"
        return self._filter_text in searchable

    def lessThan(self, left, right):
        col = left.column()
        if col in (0, 2, 7, 8):  # PID, PPID, Threads, Handles
            lv = int(float(left.data() or 0))
            rv = int(float(right.data() or 0))
            return lv < rv
        return super().lessThan(left, right)


class ProcessTableView(QWidget):
    process_selected = Signal(ProcessInfo)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索进程... (名称、PID、命令行)")
        self.search_box.setClearButtonEnabled(True)
        layout.addWidget(self.search_box)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 180)
        self.table.setColumnWidth(3, 65)
        self.table.setColumnWidth(7, 60)
        self.table.setColumnWidth(8, 60)

        layout.addWidget(self.table)

        self._model = ProcessTableModel()
        self._proxy = ProcessFilterProxy()
        self._proxy.setSourceModel(self._model)
        self.table.setModel(self._proxy)

        self.search_box.textChanged.connect(self._proxy.set_filter)
        self.table.selectionModel().selectionChanged.connect(self._on_selection)

    def _on_selection(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return
        proxy_row = indexes[0].row()
        source_index = self._proxy.mapToSource(self._proxy.index(proxy_row, 0))
        proc = self._model.get_process(source_index.row())
        if proc:
            self.process_selected.emit(proc)

    def update_snapshot(self, snapshot: Snapshot):
        self._model.update_processes(snapshot.processes)

    def select_pid(self, pid: int):
        proc = self._model.get_process_by_pid(pid)
        if proc:
            idx = self._model._processes.index(proc)
            proxy_index = self._proxy.mapFromSource(self._model.index(idx, 0))
            self.table.selectRow(proxy_index.row())
            self.table.scrollTo(proxy_index)
