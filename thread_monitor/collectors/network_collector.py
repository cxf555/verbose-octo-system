"""Collect network connections (TCP/UDP)."""

from ..models.process_info import NetworkConnection
from ..utils.win32_api import get_all_network_connections


def collect_network_connections() -> list[NetworkConnection]:
    """Collect all TCP/UDP connections system-wide."""
    raw = get_all_network_connections()
    connections = []
    for entry in raw:
        connections.append(NetworkConnection(
            pid=entry["pid"],
            protocol=entry["protocol"],
            family=entry["family"],
            local_addr=entry["local_addr"],
            local_port=entry["local_port"],
            remote_addr=entry["remote_addr"],
            remote_port=entry["remote_port"],
            state=entry["state_name"],
        ))
    return connections


def attach_network_to_processes(processes: list, connections: list[NetworkConnection]):
    """Attach network connections to matching processes in-place."""
    # Build PID -> connection list map
    pid_map: dict[int, list[NetworkConnection]] = {}
    for conn in connections:
        if conn.pid not in pid_map:
            pid_map[conn.pid] = []
        pid_map[conn.pid].append(conn)

    for proc in processes:
        if proc.pid in pid_map:
            proc.network_connections = pid_map[proc.pid]
