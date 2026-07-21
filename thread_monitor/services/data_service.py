"""Background data collection service using QThread."""

import time
from datetime import datetime

from PySide6.QtCore import QThread, Signal

from ..collectors.system_collector import collect_system_info
from ..collectors.process_collector import collect_processes
from ..collectors.thread_collector import collect_threads_for_all
from ..collectors.network_collector import collect_network_connections, attach_network_to_processes
from ..models.snapshot import Snapshot


class DataService(QThread):
    snapshot_ready = Signal(Snapshot)
    error_occurred = Signal(str)
    collection_started = Signal()
    collection_finished = Signal(float)  # elapsed ms

    def __init__(self, parent=None):
        super().__init__(parent)
        self._interval = 2.0  # seconds between collections
        self._running = False
        self._collect_threads = True
        self._collect_modules = False
        self._collect_handles = False
        self._collect_network = True
        self._last_snapshot: Snapshot | None = None

    @property
    def interval(self) -> float:
        return self._interval

    @interval.setter
    def interval(self, seconds: float):
        if seconds < 0.1:
            seconds = 0.1
        self._interval = seconds

    def stop_collection(self):
        self._running = False

    def run(self):
        self._running = True
        while self._running:
            t0 = time.perf_counter()
            self.collection_started.emit()

            try:
                snapshot = self._collect_snapshot()
                self._last_snapshot = snapshot
                self.snapshot_ready.emit(snapshot)
            except Exception as e:
                self.error_occurred.emit(str(e))

            elapsed = (time.perf_counter() - t0) * 1000
            self.collection_finished.emit(elapsed)

            # Sleep for the remaining interval, checking _running periodically
            sleep_remaining = self._interval - (time.perf_counter() - t0)
            while sleep_remaining > 0 and self._running:
                time.sleep(min(0.1, sleep_remaining))
                sleep_remaining = self._interval - (time.perf_counter() - t0)

    def collect_once(self, fast: bool = False) -> Snapshot:
        """Synchronous single collection. fast=True 时跳过线程和网络采集，仅获取进程列表。"""
        return self._collect_snapshot(fast=fast)

    def _collect_snapshot(self, fast: bool = False) -> Snapshot:
        snapshot = Snapshot()
        snapshot.timestamp = datetime.now()
        snapshot.system = collect_system_info()

        # Collect processes (fast, psutil-based)
        processes = collect_processes()
        snapshot.system.total_processes = len(processes)

        # Count total threads from process data
        total_threads = sum(p.thread_count for p in processes)

        # Collect thread details if enabled and not in fast mode
        if self._collect_threads and not fast:
            try:
                collect_threads_for_all(processes)
            except Exception:
                pass

        snapshot.system.total_threads = total_threads

        # Collect network connections if enabled and not in fast mode
        if self._collect_network and not fast:
            try:
                connections = collect_network_connections()
                attach_network_to_processes(processes, connections)
            except Exception:
                pass

        snapshot.processes = processes
        return snapshot

    def get_last_snapshot(self) -> Snapshot | None:
        return self._last_snapshot
