"""Collect process-level metrics using psutil."""

import os
import psutil
from ..models.process_info import ProcessInfo


def collect_processes() -> list[ProcessInfo]:
    processes = []
    seen_pids = set()

    for proc in psutil.process_iter(["pid", "name", "ppid", "cpu_percent", "memory_info",
                                      "num_threads", "create_time", "memory_full_info",
                                      "io_counters", "cpu_times", "cmdline", "exe",
                                      "status"]):
        try:
            pinfo = proc.info
            pid = pinfo["pid"]
            seen_pids.add(pid)

            p = ProcessInfo(
                pid=pid,
                name=pinfo.get("name") or "",
                parent_pid=pinfo.get("ppid"),
                full_path=pinfo.get("exe") or "",
                command_line=" ".join(pinfo.get("cmdline") or []),
                thread_count=pinfo.get("num_threads") or 0,
                cpu_percent=pinfo.get("cpu_percent") or 0.0,
            )

            # Start time
            create_time = pinfo.get("create_time")
            if create_time:
                import datetime
                p.start_time = datetime.datetime.fromtimestamp(create_time)

            # CPU times
            cpu_times = pinfo.get("cpu_times")
            if cpu_times:
                import datetime
                # Convert seconds to timedelta-like datetime for consistency
                p.cpu_user_time = _seconds_to_dt(cpu_times.user)
                p.cpu_kernel_time = _seconds_to_dt(cpu_times.system)

            # Memory
            mem_info = pinfo.get("memory_info")
            if mem_info:
                p.memory_working_set = mem_info.rss
                p.memory_virtual_size = getattr(mem_info, "vms", 0)

            mem_full = pinfo.get("memory_full_info")
            if mem_full:
                p.memory_private_bytes = getattr(mem_full, "uss", 0)
                p.memory_peak_working_set = getattr(mem_full, "peak_wset", 0)
                if hasattr(mem_full, "pagefile"):
                    pass  # pagefile usage

            # IO counters
            io_counters = pinfo.get("io_counters")
            if io_counters:
                p.io_read_bytes = io_counters.read_bytes or 0
                p.io_write_bytes = io_counters.write_bytes or 0

            # Base priority approximation from nice level
            try:
                p.base_priority = proc.nice()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            processes.append(p)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception:
            continue

    return processes


def _seconds_to_dt(seconds):
    """Convert seconds (float) to a datetime representing duration from midnight."""
    import datetime
    # Represent as time-of-day for display; actual conversion in UI
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    micro = int((seconds % 1) * 1_000_000)
    return datetime.datetime(2000, 1, 1, hours, minutes, secs, micro)
