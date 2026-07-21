"""Collect system-level metrics: CPU, memory, uptime."""

import psutil
from ..models.process_info import SystemInfo


def collect_system_info() -> SystemInfo:
    info = SystemInfo()

    info.cpu_percent = psutil.cpu_percent(interval=0)
    info.cpu_core_count = psutil.cpu_count(logical=True)

    mem = psutil.virtual_memory()
    info.memory_total = mem.total
    info.memory_available = mem.available
    info.memory_percent = mem.percent

    boot_time = psutil.boot_time()
    info.uptime_seconds = int(psutil.time.time() - boot_time)

    return info
