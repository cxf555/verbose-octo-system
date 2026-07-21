"""SQLite-backed history recording for process/thread metrics over time."""

import sqlite3
import json
import os
from datetime import datetime
from threading import Lock

from ..models.snapshot import Snapshot


class HistoryService:
    def __init__(self, db_path: str = ""):
        if not db_path:
            import tempfile
            db_path = os.path.join(tempfile.gettempdir(), "thread_monitor_history.db")
        self._db_path = db_path
        self._lock = Lock()
        self._init_db()

    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    total_processes INTEGER,
                    total_threads INTEGER
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS process_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER,
                    pid INTEGER,
                    name TEXT,
                    cpu_percent REAL,
                    working_set_mb REAL,
                    thread_count INTEGER,
                    handle_count INTEGER,
                    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS thread_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER,
                    pid INTEGER,
                    tid INTEGER,
                    base_priority INTEGER,
                    context_switches INTEGER,
                    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
                )
            """)
            conn.commit()
            conn.close()

    def record_snapshot(self, snapshot: Snapshot):
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO snapshots (timestamp, cpu_percent, memory_percent, total_processes, total_threads) VALUES (?, ?, ?, ?, ?)",
                (snapshot.timestamp.isoformat(), snapshot.system.cpu_percent,
                 snapshot.system.memory_percent, snapshot.system.total_processes,
                 snapshot.system.total_threads)
            )
            snap_id = cur.lastrowid

            for proc in snapshot.processes:
                cur.execute(
                    "INSERT INTO process_snapshots (snapshot_id, pid, name, cpu_percent, working_set_mb, thread_count, handle_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (snap_id, proc.pid, proc.name, proc.cpu_percent,
                     proc.memory_working_set / 1024 / 1024,
                     proc.thread_count, proc.handle_count)
                )
                for t in proc.threads:
                    cur.execute(
                        "INSERT INTO thread_snapshots (snapshot_id, pid, tid, base_priority, context_switches) VALUES (?, ?, ?, ?, ?)",
                        (snap_id, proc.pid, t.tid, t.base_priority, t.context_switches)
                    )

            conn.commit()
            conn.close()

    def get_recent_snapshots(self, limit: int = 100):
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM snapshots ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            conn.close()
            return [dict(r) for r in reversed(rows)]

    def get_process_history(self, pid: int, limit: int = 100):
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT s.timestamp, p.cpu_percent, p.working_set_mb, p.thread_count, p.handle_count
                FROM process_snapshots p
                JOIN snapshots s ON p.snapshot_id = s.id
                WHERE p.pid = ?
                ORDER BY s.id DESC
                LIMIT ?
            """, (pid, limit)).fetchall()
            conn.close()
            return [dict(r) for r in reversed(rows)]
