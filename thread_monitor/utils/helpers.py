"""Formatting and conversion helpers."""

import os
from datetime import datetime, timezone


def format_bytes(n):
    """Format bytes to human-readable string."""
    if n is None:
        return "N/A"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def format_cpu_percent(value):
    """Format CPU percent value."""
    if value is None:
        return "N/A"
    return f"{value:.1f}%"


def format_duration(delta):
    """Format a timedelta to human-readable string."""
    if delta is None:
        return "N/A"
    total_seconds = int(delta.total_seconds())
    if total_seconds < 0:
        return "0s"
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)
    if days > 0:
        return f"{days}d {hours}h {mins}m"
    if hours > 0:
        return f"{hours}h {mins}m {secs}s"
    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"


def format_number(n):
    """Format a large number with commas."""
    if n is None:
        return "N/A"
    return f"{n:,}"


def format_datetime(dt):
    """Format datetime to string."""
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_hex(value, bits=None):
    """Format integer as hex string."""
    if value is None:
        return "N/A"
    if bits:
        return f"0x{value:0{bits//4}X}"
    return f"0x{value:X}"


def get_process_priority_name(base_priority):
    """Map Windows base priority class to a human-readable name."""
    if base_priority >= 26:
        return "Realtime"
    if base_priority >= 24:
        return "High"
    if base_priority >= 13:
        return "Above Normal"
    if base_priority >= 10:
        return "Normal"
    if base_priority >= 8:
        return "Below Normal"
    if base_priority >= 6:
        return "Low"
    return "Idle"


def safe_int(value, default=0):
    """Convert value to int, returning default on error."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """Convert value to float, returning default on error."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def cpu_affinity_to_cores(mask):
    """Convert an affinity bitmask to a list of core indices."""
    if mask is None:
        return []
    cores = []
    bit = 0
    while mask:
        if mask & 1:
            cores.append(bit)
        mask >>= 1
        bit += 1
    return cores


def cores_to_affinity(cores):
    """Convert a list of core indices to an affinity bitmask."""
    mask = 0
    for core in cores:
        mask |= (1 << core)
    return mask
