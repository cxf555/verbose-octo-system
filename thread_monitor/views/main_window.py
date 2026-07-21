"""Main window with menus, toolbar, dock layout."""

import os
import ctypes

from PySide6.QtWidgets import (
    QMainWindow, QMenuBar, QMenu, QToolBar, QStatusBar,
    QSplitter, QDockWidget, QWidget, QVBoxLayout, QMessageBox,
    QFileDialog, QLabel, QComboBox, QPushButton, QHBoxLayout,
    QApplication, QStyle,
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QKeySequence, QIcon

from ..models.snapshot import Snapshot
from ..models.process_info import ProcessInfo, ThreadInfo
from ..services.data_service import DataService
from ..services.export_service import export_processes_csv, export_threads_csv, export_snapshot_json
from ..services.history_service import HistoryService

from .dashboard import Dashboard
from .process_table import ProcessTableView
from .thread_table import ThreadTableView
from .detail_panel import DetailPanel
from .cpu_chart import CpuChart
from .affinity_dialog import AffinityDialog
from .theme import DARK_THEME, LIGHT_THEME

from ..utils.win32_api import (
    kernel32, enable_debug_privilege,
    query_thread_basic_info,
)
from ..utils.win32_constants import (
    THREAD_SET_INFORMATION, THREAD_SUSPEND_RESUME, THREAD_TERMINATE,
    PROCESS_SUSPEND_RESUME,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("线程监控器")
        self.resize(1600, 950)

        self._dark_mode = True
        self._data_service = DataService()
        self._history_service = HistoryService()
        self._history_enabled = False
        self._current_process: ProcessInfo | None = None
        self._current_thread: ThreadInfo | None = None

        self._setup_ui()
        self._setup_connections()
        self._apply_theme()

        self._has_debug_priv = enable_debug_privilege()
        if not self._has_debug_priv:
            self.statusBar().showMessage(
                "警告：未以管理员权限运行，部分功能（线程挂起/恢复、句柄枚举）将受限。"
            )

        self._do_manual_refresh(fast=True)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)

        toolbar_layout = QHBoxLayout()
        self._interval_combo = QComboBox()
        self._interval_combo.addItems(["1秒", "2秒", "3秒", "5秒", "10秒"])
        self._interval_combo.setCurrentIndex(1)

        self._auto_refresh_btn = QPushButton("自动刷新")
        self._auto_refresh_btn.setCheckable(True)
        self._manual_refresh_btn = QPushButton("手动刷新 (F5)")
        self._pause_btn = QPushButton("暂停")
        self._pause_btn.setCheckable(True)
        self._pause_btn.setEnabled(False)

        toolbar_layout.addWidget(QLabel("刷新间隔:"))
        toolbar_layout.addWidget(self._interval_combo)
        toolbar_layout.addWidget(self._auto_refresh_btn)
        toolbar_layout.addWidget(self._manual_refresh_btn)
        toolbar_layout.addWidget(self._pause_btn)
        toolbar_layout.addStretch()

        self._status_info = QLabel("就绪")
        toolbar_layout.addWidget(self._status_info)
        main_layout.addLayout(toolbar_layout)

        main_splitter = QSplitter(Qt.Horizontal)

        left_splitter = QSplitter(Qt.Vertical)
        self._process_view = ProcessTableView()
        self._thread_view = ThreadTableView()
        left_splitter.addWidget(self._process_view)
        left_splitter.addWidget(self._thread_view)
        left_splitter.setStretchFactor(0, 5)   # 进程表
        left_splitter.setStretchFactor(1, 6)   # 线程表 - 放大

        main_splitter.addWidget(left_splitter)

        right_splitter = QSplitter(Qt.Vertical)
        self._detail_panel = DetailPanel()
        self._cpu_chart = CpuChart()
        self._dashboard = Dashboard()

        right_splitter.addWidget(self._dashboard)
        right_splitter.addWidget(self._detail_panel)
        right_splitter.addWidget(self._cpu_chart)
        right_splitter.setStretchFactor(0, 1)   # 仪表盘 - 缩小
        right_splitter.setStretchFactor(1, 6)   # 详情面板
        right_splitter.setStretchFactor(2, 3)   # CPU 图表

        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(0, 7)   # 左侧 (进程+线程)
        main_splitter.setStretchFactor(1, 3)   # 右侧 (详情+图表)

        main_layout.addWidget(main_splitter)

        self.statusBar().showMessage("就绪")

        self._setup_menus()

    def _setup_menus(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("文件(&F)")

        export_proc_action = QAction("导出进程列表 (CSV)...", self)
        export_proc_action.triggered.connect(self._export_processes_csv)
        file_menu.addAction(export_proc_action)

        export_thread_action = QAction("导出线程列表 (CSV)...", self)
        export_thread_action.triggered.connect(self._export_threads_csv)
        file_menu.addAction(export_thread_action)

        export_json_action = QAction("导出快照 (JSON)...", self)
        export_json_action.triggered.connect(self._export_snapshot_json)
        file_menu.addAction(export_json_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menu_bar.addMenu("视图(&V)")

        toggle_theme = QAction("切换暗色/亮色主题", self)
        toggle_theme.triggered.connect(self._toggle_theme)
        view_menu.addAction(toggle_theme)

        view_menu.addSeparator()

        history_action = QAction("启用历史记录", self)
        history_action.setCheckable(True)
        history_action.toggled.connect(self._toggle_history)
        view_menu.addAction(history_action)

        actions_menu = menu_bar.addMenu("操作(&A)")

        suspend_action = QAction("挂起选中线程", self)
        suspend_action.triggered.connect(self._suspend_thread)
        actions_menu.addAction(suspend_action)

        resume_action = QAction("恢复选中线程", self)
        resume_action.triggered.connect(self._resume_thread)
        actions_menu.addAction(resume_action)

        terminate_action = QAction("终止选中线程", self)
        terminate_action.triggered.connect(self._terminate_thread)
        actions_menu.addAction(terminate_action)

        actions_menu.addSeparator()

        affinity_action = QAction("设置 CPU 亲和性...", self)
        affinity_action.triggered.connect(self._set_thread_affinity)
        actions_menu.addAction(affinity_action)

        io_prio_menu = actions_menu.addMenu("设置 IO 优先级")
        for name, val in [("非常低", 0), ("低", 1), ("正常", 2), ("高", 3), ("关键", 4)]:
            action = QAction(name, self)
            action.setData(val)
            action.triggered.connect(lambda checked, v=val: self._set_io_priority(v))
            io_prio_menu.addAction(action)

        actions_menu.addSeparator()

        refresh_action = QAction("刷新", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self._do_manual_refresh)
        actions_menu.addAction(refresh_action)

        help_menu = menu_bar.addMenu("帮助(&H)")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_connections(self):
        self._process_view.process_selected.connect(self._on_process_selected)
        self._thread_view.thread_selected.connect(self._on_thread_selected)
        self._auto_refresh_btn.toggled.connect(self._on_auto_refresh_toggled)
        self._manual_refresh_btn.clicked.connect(self._do_manual_refresh)
        self._pause_btn.toggled.connect(self._on_pause_toggled)
        self._interval_combo.currentTextChanged.connect(self._on_interval_changed)
        self._data_service.snapshot_ready.connect(self._on_snapshot_ready)
        self._data_service.error_occurred.connect(self._on_collection_error)
        self._data_service.collection_finished.connect(self._on_collection_finished)

    def _apply_theme(self):
        theme = DARK_THEME if self._dark_mode else LIGHT_THEME
        self.setStyleSheet(theme)

    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        self._apply_theme()

    def _toggle_history(self, enabled: bool):
        self._history_enabled = enabled
        if enabled:
            self.statusBar().showMessage("历史记录已开启")
        else:
            self.statusBar().showMessage("历史记录已关闭")

    @Slot()
    def _do_manual_refresh(self, fast: bool = False):
        self._status_info.setText("采集中...")
        snapshot = self._data_service.collect_once(fast=fast)
        self._apply_snapshot(snapshot)
        self._status_info.setText(f"上次刷新: {snapshot.timestamp.strftime('%H:%M:%S')}")

    def _start_auto_refresh(self):
        interval_str = self._interval_combo.currentText()
        interval = float(interval_str.replace("秒", ""))
        self._data_service.interval = interval
        self._data_service.start()
        self._auto_refresh_btn.setChecked(True)
        self._auto_refresh_btn.setText("自动刷新 (开)")
        self._auto_refresh_btn.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e;")
        self._pause_btn.setEnabled(True)
        self._status_info.setText("自动刷新运行中...")

    def _on_auto_refresh_toggled(self, checked: bool):
        if checked:
            interval_str = self._interval_combo.currentText()
            interval = float(interval_str.replace("秒", ""))
            self._data_service.interval = interval
            self._data_service.start()
            self._auto_refresh_btn.setText("自动刷新 (开)")
            self._auto_refresh_btn.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e;")
            self._pause_btn.setEnabled(True)
            self._status_info.setText("自动刷新运行中...")
        else:
            self._data_service.stop_collection()
            self._data_service.wait(1000)
            self._auto_refresh_btn.setText("自动刷新")
            self._auto_refresh_btn.setStyleSheet("")
            self._pause_btn.setEnabled(False)
            self._pause_btn.setChecked(False)
            self._status_info.setText("自动刷新已停止")

    def _on_pause_toggled(self, checked: bool):
        if checked:
            self._data_service.stop_collection()
            self._pause_btn.setText("继续")
            self._status_info.setText("已暂停")
        else:
            self._data_service.start()
            self._pause_btn.setText("暂停")
            self._status_info.setText("自动刷新运行中...")

    def _on_interval_changed(self, text: str):
        interval = float(text.replace("秒", ""))
        self._data_service.interval = interval

    @Slot(Snapshot)
    def _on_snapshot_ready(self, snapshot: Snapshot):
        self._apply_snapshot(snapshot)

    def _apply_snapshot(self, snapshot: Snapshot):
        self._dashboard.update_from_snapshot(snapshot)
        self._cpu_chart.add_point(snapshot)

        selected_pid = None
        if self._current_process:
            selected_pid = self._current_process.pid

        self._process_view.update_snapshot(snapshot)

        if selected_pid:
            self._process_view.select_pid(selected_pid)
            proc = next((p for p in snapshot.processes if p.pid == selected_pid), None)
            if proc:
                self._thread_view.show_threads_for_process(proc)
        else:
            # 首次加载：自动选中第一个有线程的进程
            for p in snapshot.processes:
                if p.threads:
                    self._process_view.select_pid(p.pid)
                    self._thread_view.show_threads_for_process(p)
                    self._current_process = p
                    break

        if self._history_enabled:
            self._history_service.record_snapshot(snapshot)

    def _on_collection_error(self, error: str):
        self._status_info.setText(f"错误: {error}")

    def _on_collection_finished(self, elapsed_ms: float):
        self._status_info.setText(f"采集耗时: {elapsed_ms:.0f}ms")

    def _on_process_selected(self, proc: ProcessInfo):
        self._current_process = proc
        self._current_thread = None
        self._detail_panel.show_process(proc)
        self._thread_view.show_threads_for_process(proc)

    def _on_thread_selected(self, thread: ThreadInfo):
        self._current_thread = thread
        self._detail_panel.show_thread(thread)

    def _get_selected_thread_info(self):
        if not self._current_thread:
            QMessageBox.information(self, "提示", "请先选择一个线程。")
            return None
        return self._current_thread

    def _suspend_thread(self):
        ti = self._get_selected_thread_info()
        if not ti:
            return
        h = kernel32.OpenThread(THREAD_SUSPEND_RESUME, False, ti.tid)
        if not h:
            QMessageBox.warning(self, "错误", f"无法打开线程 {ti.tid}，请尝试以管理员身份运行。")
            return
        count = kernel32.SuspendThread(h)
        kernel32.CloseHandle(h)
        if count == -1:
            QMessageBox.warning(self, "错误", f"挂起线程 {ti.tid} 失败。")
        else:
            ti.suspend_count = count + 1
            self._detail_panel.show_thread(ti)
            self.statusBar().showMessage(f"线程 {ti.tid} 已挂起（计数: {ti.suspend_count}）")

    def _resume_thread(self):
        ti = self._get_selected_thread_info()
        if not ti:
            return
        h = kernel32.OpenThread(THREAD_SUSPEND_RESUME, False, ti.tid)
        if not h:
            QMessageBox.warning(self, "错误", f"无法打开线程 {ti.tid}，请尝试以管理员身份运行。")
            return
        count = kernel32.ResumeThread(h)
        kernel32.CloseHandle(h)
        if count == -1:
            QMessageBox.warning(self, "错误", f"恢复线程 {ti.tid} 失败。")
        else:
            ti.suspend_count = max(0, count - 1)
            self._detail_panel.show_thread(ti)
            self.statusBar().showMessage(f"线程 {ti.tid} 已恢复（计数: {ti.suspend_count}）")

    def _terminate_thread(self):
        ti = self._get_selected_thread_info()
        if not ti:
            return
        reply = QMessageBox.question(
            self, "确认",
            f"确定要终止线程 {ti.tid} 吗？\n\n这可能导致目标进程不稳定。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        h = kernel32.OpenThread(THREAD_TERMINATE, False, ti.tid)
        if not h:
            QMessageBox.warning(self, "错误", f"无法打开线程 {ti.tid}，请尝试以管理员身份运行。")
            return
        result = kernel32.TerminateThread(h, 0)
        kernel32.CloseHandle(h)
        if result:
            self.statusBar().showMessage(f"线程 {ti.tid} 已终止")
        else:
            QMessageBox.warning(self, "错误", f"终止线程 {ti.tid} 失败。")

    def _set_thread_affinity(self):
        ti = self._get_selected_thread_info()
        if not ti:
            return
        current_mask = ti.affinity_mask or 0
        dlg = AffinityDialog(current_mask, parent=self)
        if dlg.exec():
            new_mask = dlg.result_mask
            h = kernel32.OpenThread(THREAD_SET_INFORMATION, False, ti.tid)
            if h:
                kernel32.SetThreadAffinityMask(h, new_mask)
                kernel32.CloseHandle(h)
                ti.affinity_mask = new_mask
                self._detail_panel.show_thread(ti)
                self.statusBar().showMessage(f"线程 {ti.tid} 亲和性已设置为 0x{new_mask:X}")
            else:
                QMessageBox.warning(self, "错误", f"无法打开线程 {ti.tid}。")

    def _set_io_priority(self, priority: int):
        ti = self._get_selected_thread_info()
        if not ti:
            return
        from ..utils.win32_api import set_thread_io_priority
        h = kernel32.OpenThread(THREAD_SET_INFORMATION, False, ti.tid)
        if not h:
            QMessageBox.warning(self, "错误", f"无法打开线程 {ti.tid}。")
            return
        try:
            set_thread_io_priority(h, priority)
            ti.io_priority = priority
            self._detail_panel.show_thread(ti)
            self.statusBar().showMessage(f"线程 {ti.tid} IO 优先级已设置")
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))
        finally:
            kernel32.CloseHandle(h)

    def _export_processes_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出进程列表 CSV", "processes.csv", "CSV (*.csv)")
        if not path:
            return
        snapshot = self._data_service.get_last_snapshot()
        if not snapshot:
            QMessageBox.warning(self, "错误", "没有可导出的数据，请先刷新。")
            return
        export_processes_csv(snapshot, path)
        self.statusBar().showMessage(f"已导出至 {path}")

    def _export_threads_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出线程列表 CSV", "threads.csv", "CSV (*.csv)")
        if not path:
            return
        snapshot = self._data_service.get_last_snapshot()
        if not snapshot:
            QMessageBox.warning(self, "错误", "没有可导出的数据，请先刷新。")
            return
        export_threads_csv(snapshot, path)
        self.statusBar().showMessage(f"已导出至 {path}")

    def _export_snapshot_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出快照 JSON", "snapshot.json", "JSON (*.json)")
        if not path:
            return
        snapshot = self._data_service.get_last_snapshot()
        if not snapshot:
            QMessageBox.warning(self, "错误", "没有可导出的数据，请先刷新。")
            return
        export_snapshot_json(snapshot, path)
        self.statusBar().showMessage(f"已导出至 {path}")

    def _show_about(self):
        QMessageBox.about(self, "关于 线程监控器",
                          "<h3>线程监控器</h3>"
                          "<p>Windows 进程与线程监控工具。</p>"
                          "<p>基于 Python + PySide6 + psutil 构建。</p>")

    def closeEvent(self, event):
        self._data_service.stop_collection()
        self._data_service.wait(2000)
        event.accept()
