"""Export snapshot data to CSV or JSON."""

import csv
import json
import os
from datetime import datetime
from io import StringIO

from ..models.snapshot import Snapshot
from ..models.process_info import ProcessInfo, ThreadInfo, NetworkConnection


def export_processes_csv(snapshot: Snapshot, filepath: str):
    """Export process list to CSV."""
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "PID", "Name", "Parent PID", "Threads", "CPU%", "Working Set (MB)",
            "Private Bytes (MB)", "Virtual Size (MB)", "Handles",
            "Start Time", "Running Time", "Command Line"
        ])
        for proc in snapshot.processes:
            writer.writerow([
                proc.pid, proc.name, proc.parent_pid or "",
                proc.thread_count, f"{proc.cpu_percent:.2f}",
                f"{proc.memory_working_set / 1024 / 1024:.2f}",
                f"{proc.memory_private_bytes / 1024 / 1024:.2f}",
                f"{proc.memory_virtual_size / 1024 / 1024:.2f}",
                proc.handle_count,
                proc.start_time.strftime("%Y-%m-%d %H:%M:%S") if proc.start_time else "",
                str(proc.running_time) if proc.running_time else "",
                proc.command_line,
            ])


def export_threads_csv(snapshot: Snapshot, filepath: str):
    """Export all threads to CSV."""
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "PID", "Process", "TID", "CPU User Time", "CPU Kernel Time",
            "Base Priority", "Dynamic Priority", "IO Priority", "Page Priority",
            "Context Switches", "Start Address", "Affinity Mask"
        ])
        for proc in snapshot.processes:
            for t in proc.threads:
                writer.writerow([
                    proc.pid, proc.name, t.tid,
                    str(t.cpu_user_time), str(t.cpu_kernel_time),
                    t.base_priority, t.dynamic_priority,
                    t.io_priority or "", t.page_priority or "",
                    t.context_switches,
                    f"0x{t.start_address:X}" if t.start_address else "",
                    f"0x{t.affinity_mask:X}" if t.affinity_mask else "",
                ])


def export_snapshot_json(snapshot: Snapshot, filepath: str):
    """Export full snapshot to JSON."""
    data = {
        "timestamp": snapshot.timestamp.isoformat(),
        "system": {
            "cpu_percent": snapshot.system.cpu_percent,
            "memory_percent": snapshot.system.memory_percent,
            "memory_total_gb": snapshot.system.memory_total / 1024**3,
            "total_processes": snapshot.system.total_processes,
            "total_threads": snapshot.system.total_threads,
            "total_handles": snapshot.system.total_handles,
            "uptime_seconds": snapshot.system.uptime_seconds,
        },
        "processes": []
    }

    for proc in snapshot.processes:
        pdata = {
            "pid": proc.pid,
            "name": proc.name,
            "parent_pid": proc.parent_pid,
            "full_path": proc.full_path,
            "command_line": proc.command_line,
            "thread_count": proc.thread_count,
            "handle_count": proc.handle_count,
            "cpu_percent": proc.cpu_percent,
            "memory_working_set_mb": proc.memory_working_set / 1024 / 1024,
            "memory_private_bytes_mb": proc.memory_private_bytes / 1024 / 1024,
            "memory_virtual_size_mb": proc.memory_virtual_size / 1024 / 1024,
            "start_time": proc.start_time.isoformat() if proc.start_time else None,
            "running_time": str(proc.running_time) if proc.running_time else None,
            "threads": [
                {
                    "tid": t.tid,
                    "base_priority": t.base_priority,
                    "dynamic_priority": t.dynamic_priority,
                    "context_switches": t.context_switches,
                    "start_address": f"0x{t.start_address:X}" if t.start_address else None,
                }
                for t in proc.threads
            ],
            "network_connections": [
                {
                    "protocol": nc.protocol,
                    "local_addr": nc.local_addr,
                    "local_port": nc.local_port,
                    "remote_addr": nc.remote_addr,
                    "remote_port": nc.remote_port,
                    "state": nc.state,
                }
                for nc in proc.network_connections
            ],
        }
        data["processes"].append(pdata)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
