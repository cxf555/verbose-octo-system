"""Data models for process/thread monitoring."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ThreadInfo:
    tid: int
    pid: int
    cpu_percent: float = 0.0
    cpu_user_time: Optional[datetime] = None
    cpu_kernel_time: Optional[datetime] = None
    base_priority: int = 0
    dynamic_priority: int = 0
    io_priority: Optional[int] = None
    page_priority: Optional[int] = None
    thread_state: str = ""
    wait_reason: str = ""
    context_switches: int = 0
    context_switch_delta: int = 0  # delta since last snapshot
    start_address: Optional[int] = None
    affinity_mask: Optional[int] = None
    cycle_time: Optional[int] = None
    suspend_count: int = 0
    is_suspicious: bool = False

    @property
    def total_cpu_time_ms(self) -> float:
        """Total CPU time (user + kernel) in milliseconds."""
        total = 0.0
        if self.cpu_user_time:
            total += self.cpu_user_time.hour * 3600000 + self.cpu_user_time.minute * 60000 + \
                     self.cpu_user_time.second * 1000 + self.cpu_user_time.microsecond / 1000
        if self.cpu_kernel_time:
            total += self.cpu_kernel_time.hour * 3600000 + self.cpu_kernel_time.minute * 60000 + \
                     self.cpu_kernel_time.second * 1000 + self.cpu_kernel_time.microsecond / 1000
        return total


@dataclass
class ModuleInfo:
    name: str
    path: str
    base_address: int
    size: int
    pid: int


@dataclass
class HandleInfo:
    handle_value: int
    handle_type: str
    object_name: str = ""
    granted_access: int = 0


@dataclass
class NetworkConnection:
    pid: int
    protocol: str  # "TCP" or "UDP"
    family: str  # "IPv4" or "IPv6"
    local_addr: str
    local_port: int
    remote_addr: str
    remote_port: int
    state: str  # "LISTEN", "ESTABLISHED", etc. (empty for UDP)

    @property
    def display_string(self) -> str:
        if self.protocol == "UDP":
            return f"{self.local_addr}:{self.local_port}"
        return f"{self.local_addr}:{self.local_port} -> {self.remote_addr}:{self.remote_port} [{self.state}]"


@dataclass
class ProcessInfo:
    pid: int
    name: str
    parent_pid: Optional[int] = None
    full_path: str = ""
    command_line: str = ""
    thread_count: int = 0
    handle_count: int = 0
    cpu_percent: float = 0.0
    cpu_user_time: Optional[datetime] = None
    cpu_kernel_time: Optional[datetime] = None
    cpu_total_delta: float = 0.0  # delta total ms since last snapshot
    memory_working_set: int = 0
    memory_private_bytes: int = 0
    memory_virtual_size: int = 0
    memory_peak_working_set: int = 0
    page_faults: int = 0
    io_read_bytes: int = 0
    io_write_bytes: int = 0
    base_priority: int = 0
    session_id: int = 0
    start_time: Optional[datetime] = None
    gdi_objects: int = 0
    user_objects: int = 0
    integrity_level: str = ""
    dep_enabled: bool = False
    aslr_enabled: bool = False
    is_suspicious: bool = False

    # sub-items
    threads: list[ThreadInfo] = field(default_factory=list)
    modules: list[ModuleInfo] = field(default_factory=list)
    handles: list[HandleInfo] = field(default_factory=list)
    network_connections: list[NetworkConnection] = field(default_factory=list)

    @property
    def running_time(self):
        if self.start_time is None:
            return None
        return datetime.now() - self.start_time

    @property
    def total_cpu_time_ms(self) -> float:
        total = 0.0
        if self.cpu_user_time:
            total += self.cpu_user_time.hour * 3600000 + self.cpu_user_time.minute * 60000 + \
                     self.cpu_user_time.second * 1000 + self.cpu_user_time.microsecond / 1000
        if self.cpu_kernel_time:
            total += self.cpu_kernel_time.hour * 3600000 + self.cpu_kernel_time.minute * 60000 + \
                     self.cpu_kernel_time.second * 1000 + self.cpu_kernel_time.microsecond / 1000
        return total


@dataclass
class SystemInfo:
    cpu_percent: float = 0.0
    memory_total: int = 0
    memory_available: int = 0
    memory_percent: float = 0.0
    total_processes: int = 0
    total_threads: int = 0
    total_handles: int = 0
    cpu_core_count: int = 0
    uptime_seconds: int = 0


